import os,sys
import numpy as np
import logging
from PIL import Image
from optparse import OptionParser

import paddle.utils.image_util as image_util

from py_paddle import swig_paddle, DataProviderConverter
from paddle.trainer.PyDataProvider2 import dense_vector
from paddle.trainer.config_parser import parse_config

logging.basicConfig(format='[%(levelname)s %(asctime)s %(filename)s:%(lineno)s] %(message)s')
logging.getLogger().setLevel(logging.INFO)

class ImageClassifier():
    def __init__(self,
                 train_conf,
                 use_gpu=True,
                 model_dir=None,
                 resize_dim=None,
                 crop_dim=None,
                 mean_file=None,
                 oversample=False,
                 is_color=False):
        """
        train_conf: network configure.
        model_dir: string, directory of model.
        resize_dim: int, resized image size.
        crop_dim: int, crop size.
        mean_file: string, image mean file.
        oversample: bool, oversample means multiple crops, namely five
                    patches (the four corner patches and the center
                    patch) as well as their horizontal reflections,
                    ten crops in all.
        """
        self.train_conf = train_conf
        self.model_dir = model_dir
        if model_dir is None:
            self.model_dir = os.path.dirname(train_conf)

        self.resize_dim = resize_dim
        self.crop_dims = [crop_dim, crop_dim]
        self.oversample = oversample
        self.is_color = is_color

        self.transformer = image_util.ImageTransformer(is_color = is_color)
        self.transformer.set_transpose((2,0,1))

        self.mean_file = mean_file
        mean = np.load(self.mean_file)['data_mean']
        mean = mean.reshape(1, self.crop_dims[0], self.crop_dims[1])
        self.transformer.set_mean(mean) # mean pixel
        gpu = 1 if use_gpu else 0
        conf_args = "is_test=1,use_gpu=%d,is_predict=1" % (gpu)
        conf = parse_config(train_conf, conf_args)
        swig_paddle.initPaddle("--use_gpu=%d" % (gpu))
        self.network = swig_paddle.GradientMachine.createFromConfigProto(conf.model_config)
        assert isinstance(self.network, swig_paddle.GradientMachine)
        self.network.loadParameters(self.model_dir)

        data_size = 1 * self.crop_dims[0] * self.crop_dims[1]
        slots = [dense_vector(data_size)]
        self.converter = DataProviderConverter(slots)

    def get_data(self, img_path):
        """
        1. load image from img_path.
        2. resize or oversampling.
        3. transformer data: transpose, sub mean.
        return K x H x W ndarray.
        img_path: image path.
        """
        image = image_util.load_image(img_path, self.is_color)
        if self.oversample:
            # image_util.resize_image: short side is self.resize_dim
            image = image_util.resize_image(image, self.resize_dim)
            image = np.array(image)
            input = np.zeros((1, image.shape[0], image.shape[1],1),
                             dtype=np.float32)
	    if self.is_color:
            	input[0] = image.astype(np.float32)
	    else:
	    	for i in range(0,self.resize_dim):
		    for j in range(0,self.resize_dim):
		        input[0][i][j][0]=image[i][j]
            input = image_util.oversample(input, self.crop_dims)
        else:
            image = image.resize(self.crop_dims, Image.ANTIALIAS)
	    image = np.array(image)
            input = np.zeros((1, self.crop_dims[0], self.crop_dims[1],1),
                             dtype=np.float32)
	    if self.is_color:
            	input[0] = image.astype(np.float32)
	    else:
	    	for i in range(0,self.resize_dim):
		    for j in range(0,self.resize_dim):
		        input[0][i][j][0]=image[i][j]

        data_in = []
        for img in input:
            img = self.transformer.transformer(img).flatten()
            data_in.append([img.tolist()])
        return data_in

    def forward(self, input_data):
        in_arg = self.converter(input_data)
        return self.network.forwardTest(in_arg)

    def forward(self, data, output_layer):
        """
        input_data: py_paddle input data.
        output_layer: specify the name of probability, namely the layer with
                      softmax activation.
        return: the predicting probability of each label.
        """
        input = self.converter(data)
        self.network.forwardTest(input)
        output = self.network.getLayerOutputs(output_layer)
        # For oversampling, average predictions across crops.
        # If not, the shape of output[name]: (1, class_number),
        # the mean is also applicable.
        return output[output_layer].mean(0)

    def predict(self, image=None, output_layer=None):
        assert isinstance(image, basestring)
        assert isinstance(output_layer, basestring)
        data = self.get_data(image)
        prob = self.forward(data, output_layer)
        lab = np.argsort(-prob)
        logging.info("Label of %s is: %d", image, lab[0])

if __name__ == '__main__':
    image_size=28
    crop_size=28
    multi_crop=0
    config="vgg_16_captcha.py"
    output_layer="__fc_layer_1__"
    mean_path="data/batches/batches.meta"
    model_path=sys.argv[1]
    image=sys.argv[2]
    use_gpu=bool(int(sys.argv[3]))

    obj = ImageClassifier(train_conf=config,
                          model_dir=model_path,
                          resize_dim=image_size,
                          crop_dim=crop_size,
                          mean_file=mean_path,
                          use_gpu=use_gpu,
                          oversample=multi_crop)
    obj.predict(image, output_layer)
