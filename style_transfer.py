import os
import argparse
import logging
import configparser

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


def _download_file_from_blob(bsc, container_nm, blob_file, dn_file):
    logging.info('downlod: {} -> {}'.format(blob_file, dn_file))

    if os.path.exists(dn_file):
        logging.info('already file: {}'.format(dn_file))
        return

    blob_client = bsc.get_blob_client(container=container_nm, blob=blob_file)
    with open(dn_file, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())


def get_conf(conf_file, storage_conn_str):
    if not os.path.exists(conf_file):
        logging.info('downlod conf file: {}'.format(conf_file))
        blob_service_client = BlobServiceClient.from_connection_string(storage_conn_str)
        conf_blob = os.path.join('app', 'conf.ini')
        _download_file_from_blob(blob_service_client, 'art-set', conf_blob, conf_file)
    
    config = configparser.ConfigParser()
    config.read(conf_file)
    return dict(config['Default'])


def style_transfer(style_blob, content_blob, storage_conn_str, config):
    image_ct_nm = config['image_container_name']
    model_ct_nm = config['model_container_name']
    transfer_ct_nm = config['transfer_container_name']
    model_blob = config['model_blob']

    dn_style = os.path.basename(style_blob)
    dn_content = os.path.basename(content_blob)
    dn_model = os.path.basename(model_blob)

    blob_dir = os.path.dirname(style_blob)

    transfer_file = '_'.join(['transfer', dn_style.split('.')[0], dn_content.split('.')[0]]) + '.' + dn_style.split('.')[-1]

    blob_service_client = BlobServiceClient.from_connection_string(storage_conn_str)
    if not os.path.exists(transfer_file):
        _download_file_from_blob(blob_service_client, image_ct_nm, style_blob, dn_style)
        _download_file_from_blob(blob_service_client, image_ct_nm, content_blob, dn_content)
        _download_file_from_blob(blob_service_client, model_ct_nm, model_blob, dn_model)

        cmd = "neural-style \
                -content_image {} -style_image {} \
                -output_image {} \
                -save_iter 25 \
                -gpu c  \
                -model_file {} \
                -image_size 256 \
                -num_iterations 200 \
                -content_weight 200 -style_weight 10".format(dn_content, dn_style, transfer_file, dn_model)
        
        logging.debug(cmd)
        ret = os.system(cmd)
        logging.debug(ret)
    else:
        logging.info('already transfer file: {}'.format(transfer_file))

    blob_transfer = os.path.join(blob_dir, transfer_file)
    blob_client = blob_service_client.get_blob_client(container=transfer_ct_nm, blob=blob_transfer)
    try:
        logging.info("upload transfer to blob: {}, {}".format(transfer_file, blob_transfer))
        with open(transfer_file, "rb") as data:
            blob_client.upload_blob(data)
    except Exception as e:
        logging.info('already transfer in blob: {}'.format(blob_transfer))
        # logging.error(e)

    return blob_transfer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='style transfer')
    parser.add_argument('--style_blob', help='style blob')
    parser.add_argument('--content_blob', help='style blob')
    parser.add_argument('--conf', help='configure')
    parser.add_argument('--storage_conn_str', help='storage connect string')

    args = parser.parse_args()
    
    style_blob= args.style_blob
    content_blob = args.content_blob
    storage_conn_str = args.storage_conn_str
    conf_file = args.conf

    config = get_conf(conf_file, storage_conn_str)
    transfer_blob = style_transfer(style_blob, content_blob, storage_conn_str, config)
    print(transfer_blob)
