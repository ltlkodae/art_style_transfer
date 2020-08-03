from flask import request
from flask import Flask
from style_transfer import style_transfer, get_conf
import configparser
import logging
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='flask for style transfer')
    parser.add_argument('--conf', help='config file')
    parser.add_argument('--storage_conn_str', help='storage connection string')

    args = parser.parse_args()
    conf_file = args.conf
    storage_conn_str = args.storage_conn_str

    config = get_conf(conf_file, storage_conn_str)

    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)s %(message)s')


@app.route('/st', methods=['GET'])
def st():
    style_blob = request.args.get('style', None)
    content_blob = request.args.get('content', None)

    if style_blob is None or content_blob is None:
        logging.error('Invalid Parameters')
        transfer_blob = None
    else:
        transfer_blob = style_transfer(style_blob, content_blob, storage_conn_str, config)

    logging.info("{}, {}, {}".format(style_blob, content_blob, transfer_blob))
    print(style_blob, content_blob, transfer_blob)
    return transfer_blob

@app.route('/')
def hello_world():
    return 'hello world'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
