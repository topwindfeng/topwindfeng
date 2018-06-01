import argparse
import atexit
import logging
import json
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils


logger_format = '%(asctime)-15s %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('data-stream')
logger.setLevel(logging.DEBUG)


def shutdown_hook(producer):
    try:
        producer.flush(10)
    except KafkaError as kafka_error:
        logger.warn('Failed to flush pending messages to kafka, caused by: %s', kafka_error.message)
    finally:
        try:
            producer.close(10)
        except Exception as e:
            logger.warn('Failed to close kafka connection, caused by %s', e.message)


def process_stream(stream, kafka_producer, target_topic):
    def send_to_kafka(rdd):
        results = rdd.collect()
        for r in results:
            data = json.dumps(
                {
                    'Symbol': r[0],
                    'Timestamp': time.time(),
                    'Average': r[1]
                })
            try:
                logger.info('Sending average price %s to kafka', data)
                kafka_producer.send(target_topic, value=data)
            except KafkaError as error:
                logger.warn('Failed to send average price to kafka, caused by: %s', error.message)


    def pair(data):
        record = json.loads(data.encode('utf-8'))
        return record.get('Symbol'), (float(record.get('LastTradePrice')), 1)  # (symbol, (price, count))

    stream.map(pair).reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])).map(lambda (k, v):(k, v[0]/v[1])).foreachRDD(send_to_kafka)



if __name__ == '__main__':

    # Setup command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('source_topic', help='the kafka topic to subscribe from.')
    parser.add_argument('target_topic', help='the kafka topic to send message to.')
    parser.add_argument('kafka_broker', help='the kafka broker.')
    parser.add_argument('batch_duration', help='the batch duration in secs.')

    # Parse arguments.
    args = parser.parse_args()
    source_topic = args.source_topic
    target_topic = args.target_topic
    kafka_broker = args.kafka_broker
    batch_duration = int(args.batch_duration)

    # Create SparkContext and SparkStreamingContext
    sc = SparkContext('local[2]', 'AveragePrice')
    sc.setLogLevel('INFO')
    ssc = StreamingContext(sc, batch_duration)

    # Instantiate a Kafka stream for processing.
    directKafkaStream = KafkaUtils.createDirectStream(ssc, [source_topic], {'metadata.broker.list':kafka_broker})

    # Extract value
    stream = directKafkaStream.map(lambda x : x[1])

    # Instantiate a simple Kafka producer.
    kafka_producer = KafkaProducer(bootstrap_servers=kafka_broker)

    process_stream(stream, kafka_producer, target_topic)

    # Setup shutdown hook
    atexit.register(shutdown_hook, kafka_producer)

    ssc.start()
    ssc.awaitTermination()









