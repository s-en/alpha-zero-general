import tensorflow as tf
from tensorflow.python.framework import graph_util
from jyungo.JyungoGame import JyungoGame as Game
from jyungo.tensorflow.NNet import NNetWrapper as nn
import shutil
from tensorflow.python.tools import freeze_graph
import os
from tensorflow.tools.graph_transforms import TransformGraph

def get_graph_def_from_file(nnet, graph_filepath):
  with nnet.nnet.graph.as_default():
    with tf.gfile.GFile(graph_filepath, 'rb') as f:
      graph_def = tf.GraphDef()
      graph_def.ParseFromString(f.read())
      is_training = tf.convert_to_tensor(False)
      tf.graph_util.import_graph_def(graph_def, input_map={'is_training': is_training}, name='')
      return graph_def

def convert_graph_def_to_saved_model(nnet, export_dir, graph_filepath):
  if tf.gfile.Exists(export_dir):
    tf.gfile.DeleteRecursively(export_dir)
  graph_def = get_graph_def_from_file(nnet, graph_filepath)
  with tf.Session(graph=tf.Graph()) as session:
    tf.import_graph_def(graph_def, name='')
    tf.saved_model.simple_save(
        session,
        export_dir,
        inputs = {
            'input_boards': nnet.nnet.input_boards,
            'is_training': nnet.nnet.isTraining
        },
        outputs = {
            'prob': nnet.nnet.prob
        }
    )
    print('Optimized graph converted to SavedModel!')

def main(argv=None):
    g = Game(5)
    nnet = nn(g)
    nnet.load_checkpoint('temp', 'best.pth.tar')

    # savedModel形式で保存
    shutil.rmtree('./saved_model', ignore_errors=False)
    with nnet.nnet.graph.as_default():
        builder = tf.saved_model.builder.SavedModelBuilder('./saved_model')
        inputs = {
            'input_boards': nnet.nnet.input_boards,
            'dropout': nnet.nnet.dropout,
            'is_training': nnet.nnet.isTraining
        }
        outputs = {
            'pi': nnet.nnet.pi,
            'prob': nnet.nnet.prob,
            'v': nnet.nnet.v
        }
        signature = tf.saved_model.predict_signature_def(inputs=inputs, outputs=outputs)
        builder.add_meta_graph_and_variables(sess=nnet.sess,
                                            tags=[tf.saved_model.tag_constants.SERVING],
                                            signature_def_map={'serving_default': signature})
        builder.save()
    # freeze model
    saved_model_dir = os.path.join(os.getcwd(), 'saved_model')
    output_filename = 'frozen_model.pb'
    output_graph_filename = os.path.join(saved_model_dir, output_filename)
    initializer_nodes = ''
    output_node_names = 'prob,v_1'

    freeze_graph.freeze_graph(input_saved_model_dir=saved_model_dir,
        output_graph=output_graph_filename,
        saved_model_tags = tf.saved_model.tag_constants.SERVING,
        output_node_names=output_node_names,
        initializer_nodes=initializer_nodes,
        input_graph=None,
        input_saver=False,
        input_binary=False, 
        input_checkpoint=None,
        restore_op_name=None,
        filename_tensor_name=None,
        clear_devices=False,
        input_meta_graph=False)
    print('graph freezed!')
    # input_names = ['input_boards', 'is_training']
    # output_names = [output_node_names]
    # transforms = [
    #     'remove_nodes(op=Identity)', 
    #     'merge_duplicate_nodes',
    #     'strip_unused_nodes',
    #     'fold_constants(ignore_errors=true)',
    #     'fold_batch_norms',
    #     #'quantize_nodes', # Quantized系の命令にtfjsが対応してないので使えない
    #     'quantize_weights'# Quantized系の命令にtfjsが対応してないので使えない
    # ]
    # graph_def = get_graph_def_from_file(nnet, os.path.join(saved_model_dir, output_filename))
    # optimized_graph_def = TransformGraph(
    #     graph_def,
    #     input_names,
    #     output_names,
    #     transforms)
    # tf.io.write_graph(optimized_graph_def,
    #                     logdir=saved_model_dir,
    #                     as_text=False,
    #                     name='optimized_model.pb')
    # print('Graph optimized!')

    # optimized_export_dir = os.path.join(saved_model_dir, 'optimized')
    # optimized_filepath = os.path.join(saved_model_dir, 'optimized_model.pb')
    # convert_graph_def_to_saved_model(nnet, optimized_export_dir, optimized_filepath)

    # この後tensorflowjs_converterでtfjs形式に変換
    # conda activate tf1
    # tensorflowjs_converter --input_format=tf_frozen_model --output_node_names=prob,v_1 C:\Users\sen\Documents\GitHub\alpha-zero-general\saved_model\frozen_model.pb C:\Users\sen\Documents\GitHub\alpha-zero-general\js_model --quantize_float16

    # tf1環境 python3.6
    # pip install tensorflow==1.15
    # pip install h5py numpy keras
    # pip install --no-deps tensorflowjs==1.7.4
    # pip install tensorflow_hub

if __name__ == '__main__':
    tf.app.run(main)