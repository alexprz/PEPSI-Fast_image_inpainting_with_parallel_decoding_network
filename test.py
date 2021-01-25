import tensorflow as tf
import scipy.misc as sci
import os
import numpy as np
import Read_Image_List as ri
import module as mm
import ops as op
import random
import time
import cv2
from torchvision.utils import make_grid
import matplotlib.pyplot as plt
import torch

from dataset import load_celeba


def imshow(img):
    plt.figure()
    plt.imshow(np.transpose(img.detach().numpy(), (1, 2, 0)))


Height = 256
Width = 256
# Height = 96
# Width = 96
# Height = 278
# Width = 178
batch_size = 8
# mask_size = 128
mask_size = 32

os.makedirs('figs/', exist_ok=True)

if __name__ == '__main__':
    # dPath_l = ('./List')

    # dPath_train = ('/train_fh256.txt')
    # dPath_test = ('/test_fh256.txt')
    # dPath_testm = ('/test_mask256.txt')
    # dPath_testf = ('/test_maskff.txt')

    name_f = load_celeba('train')
    num_f = len(name_f)

    name_test = load_celeba('small-test')
    num_test = len(name_test)

    name_tests = load_celeba('masked')
    num_tests = len(name_tests)
    x_mask = (Width - mask_size)//2
    y_mask = (Height - mask_size)//2
    xst = x_mask*np.ones(num_tests)
    yst = y_mask*np.ones(num_tests)

    print(f'{num_f} images found in train dataset.')
    print(f'{num_tests} images found in small-test dataset.')
    print(f'{num_tests} images found in masked dataset.')

    # exit()
    # name_f, num_f = ri.read_labeled_image_list(dPath_l + dPath_train)
    # name_test, num_test = ri.read_labeled_image_list(dPath_l + dPath_test)
    # name_testf, num_testf = ri.read_labeled_image_list(dPath_l + dPath_testf)
    # name_tests, num_tests, xst, yst = ri.read_labeled_image_list2(dPath_l + dPath_testm)
    total_batch = int(num_f / batch_size)

    save_path = './validation/v1'
    model_path = './model/v1'

    restore = True
    restore_point = 230  #900000
    Checkpoint = model_path + '/cVG iter ' + str(restore_point) + '/'
    WeightName = Checkpoint + 'Train_' + str(restore_point) + '.meta'

    if restore == False:
        restore_point = 0

    # saving_iter = 10
    # Max_iter = 1000000

    # ------- variables

    X = tf.placeholder(tf.float32, [batch_size, Height, Width, 3])
    Y = tf.placeholder(tf.float32, [batch_size, Height, Width, 3])

    MASK = tf.placeholder(tf.float32, [batch_size, Height, Width, 3])
    IT = tf.placeholder(tf.float32)

    # ------- structure

    input = tf.concat([X, MASK], 3)

    vec_en = mm.encoder(input, reuse=False, name='G_en')

    vec_con = mm.contextual_block(vec_en, vec_en, MASK, 3, 50.0, 'CB1', stride=1)

    I_co = mm.decoder(vec_en, Width, Height, reuse=False, name='G_de')
    I_ge = mm.decoder(vec_con, Width, Height, reuse=True, name='G_de')

    image_result = I_ge * (1-MASK) + Y*MASK

    D_real_red = mm.discriminator_red(Y, reuse=False, name='disc_red')
    D_fake_red = mm.discriminator_red(image_result, reuse=True, name='disc_red')

    # ------- Loss

    Loss_D_red = tf.reduce_mean(tf.nn.relu(1+D_fake_red)) + tf.reduce_mean(tf.nn.relu(1-D_real_red))

    Loss_D = Loss_D_red

    Loss_gan_red = -tf.reduce_mean(D_fake_red)

    Loss_gan = Loss_gan_red

    Loss_s_re = tf.reduce_mean(tf.abs(I_ge - Y))
    Loss_hat = tf.reduce_mean(tf.abs(I_co - Y))

    A = tf.image.rgb_to_yuv((image_result+1)/2.0)
    A_Y = tf.to_int32(A[:, :, :, 0:1]*255.0)

    B = tf.image.rgb_to_yuv((Y+1)/2.0)
    B_Y = tf.to_int32(B[:, :, :, 0:1]*255.0)

    ssim = tf.reduce_mean(tf.image.ssim(A_Y, B_Y, 255.0))

    # alpha = IT/Max_iter

    # Loss_G = 0.1*Loss_gan + 10*Loss_s_re + 5*(1-alpha) * Loss_hat

    # --------------------- variable & optimizer

    # var_D = [v for v in tf.global_variables() if v.name.startswith('disc_red')]
    # var_G = [v for v in tf.global_variables() if v.name.startswith('G_en') or v.name.startswith('G_de') or v.name.startswith('CB1')]

    # update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)

    # with tf.control_dependencies(update_ops):
    #     optimize_D = tf.train.AdamOptimizer(learning_rate=0.0004, beta1=0.5, beta2=0.9).minimize(Loss_D, var_list=var_D)
    #     optimize_G = tf.train.AdamOptimizer(learning_rate=0.0001, beta1=0.5, beta2=0.9).minimize(Loss_G, var_list=var_G)

    # --------- Run

    config = tf.ConfigProto()
    config.gpu_options.per_process_gpu_memory_fraction = 0.4
    config.gpu_options.allow_growth = False

    sess = tf.Session(config=config)

    init = tf.global_variables_initializer()
    sess.run(init)
    saver = tf.train.Saver()

    if restore:
        print('Weight Restoring.....')
        Restore = tf.train.import_meta_graph(WeightName)
        Restore.restore(sess, tf.train.latest_checkpoint(Checkpoint))
        print('Weight Restoring Finish!')

    psnr_l = 0
    psnr_g = 0
    psnr_f = 0
    ssim_m = 0

    for batch_id in range(2):
        # mask_sizep = 128
        mask_sizep = 32

        data_test = ri.MakeImageBlock(name_test, Height, Width, batch_id, batch_size)
        data_tempt = 255.0 * ((data_test + 1) / 2.0)
        mask_t = ri.MakeImageBlock(name_tests, Height, Width, batch_id, batch_size)
        mask_t = (mask_t + 1) / 2

        data_tempt = data_tempt * mask_t
        data_mt = (data_tempt / 255.0) * 2.0 - 1

        img_sample1, ssim_temp = sess.run([image_result, ssim], feed_dict={X: data_mt, Y: data_test, MASK: mask_t})

        # print(img_sample1)
        # print(type(img_sample1))
        # print(img_sample1.shape)

        # print(img_sample1.shape)
        # img_sample1 = np.transpose(img_sample1, (0, 3, 1, 2))
        # print(img_sample1.shape)

        grid = make_grid(torch.tensor(np.transpose(img_sample1, (0, 3, 1, 2))))
        # print(grid.size())

        imshow(grid)
        plt.axis('off')
        plt.savefig(f'figs/test-iter_{restore_point}-batch_{batch_id}.pdf', bbox_inches='tight')
        plt.savefig(f'figs/test-iter_{restore_point}-batch_{batch_id}.jpg', bbox_inches='tight')

        # print(ssim_temp)
        # print(type(ssim_temp))
        # print(ssim_temp.shape)


        for kk in range(batch_size):
            xx = int(xst[batch_id * batch_size + kk])
            yy = int(yst[batch_id * batch_size + kk])
            img_sample2 = img_sample1[:, xx:xx + mask_sizep, yy:yy + mask_sizep, :]
            img_sample3 = data_test[:, xx:xx + mask_sizep, yy:yy + mask_sizep, :]

            temp_img1 = img_sample1[kk, :, :, :]
            temp_img2 = img_sample2[kk, :, :, :]
            temp_img3 = data_test[kk, :, :, :]
            temp_img4 = img_sample3[kk, :, :, :]

            img_re = 255.0 * ((temp_img1 + 1) / 2.0)
            img_rem = 255.0 * ((temp_img2 + 1) / 2.0)
            img_gt = 255.0 * ((temp_img3 + 1) / 2.0)
            img_gtm = 255.0 * ((temp_img4 + 1) / 2.0)

            mse_l = np.mean(np.square(img_gtm - img_rem))
            mse_g = np.mean(np.square(img_gt - img_re))
            psnr_l += 10 * np.log10(255.0 * 255.0 / mse_l)
            psnr_g += 10 * np.log10(255.0 * 255.0 / mse_g)
        ssim_m += ssim_temp

    print('\nLocal = ', '%.4f' % (psnr_l/800),'\nGlobal = ', '%.4f\n' % (psnr_g/800), 'ssim = %.4f\n' % (ssim_m/100.0))