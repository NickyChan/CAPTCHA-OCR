# CAPTCHA-OCR
ͼ����֤���Զ�ʶ��ϵͳ

## ����׼��

* ubuntu����ϵͳ
* [PaddlePaddle�ĵ�](http://www.paddlepaddle.org/doc_cn/)

## �����

### ��װPaddlePaddle

* http://www.paddlepaddle.org/doc_cn/build_and_install/install/ubuntu_install.html

### ������Ŀ
```
git clone https://github.com/wangmengzhi/CAPTCHA-OCR.git
cd CAPTCHA-OCR
```

### ����MNIST��д����ѵ������
* ��Ⱥ���������غ��ѹ��data�ļ�����

### ������תΪPaddle��ʽ
```
sh preprocess.sh
```

### ѵ��
```
sh train.sh
/*
train.sh�еĲ�����������
use_gpu:�Ƿ�ʹ��gpu
trainer_count:ѵ���߳���
num_passes:ѵ������
*/
```

### Ԥ��
```
sh predict.sh
/*
predict.sh�еĲ�����������
model:Ԥ��ʹ�õ�ģ��
image:ҪԤ���ͼƬλ��
*/
```
