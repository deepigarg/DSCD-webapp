import pika
from pika.exchange_type import ExchangeType
from sqlalchemy.orm.attributes import flag_modified
from app import app, db
from app.models import Channel, Message
from flask_login import current_user
from datetime import datetime


class ExampleConsumer(object):
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.
    If RabbitMQ closes the connection, this class will stop and indicate
    that reconnection is necessary. You should look at the output, as
    there are limited reasons why the connection may be closed, which
    usually are tied to permission related issues or socket timeouts.
    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.
    """
    EXCHANGE = 'portal'
    EXCHANGE_TYPE = ExchangeType.topic

    def __init__(self, amqp_url, topic_name, inst="channel"):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.
        :param str amqp_url: The AMQP url to connect with
        """

        self.QUEUE = topic_name
        self.ROUTING_KEY = topic_name
        self.should_reconnect = False
        self.was_consuming = False

        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self._consuming = False
        # In production, experiment with higher prefetch values
        # for higher consumer throughput
        self._prefetch_count = 1
        self.num_msgs = 0
        self.inst_type = inst

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.
        :rtype: pika.SelectConnection
        """
        print('Connecting to %s', self._url)
        self._connection = pika.BlockingConnection(parameters=pika.URLParameters(self._url))

        print('Creating a new channel')
        self._channel = self._connection.channel()
        print('Channel opened')

        exchange_name = self.EXCHANGE
        # self.setup_exchange(self.EXCHANGE)
        print('Declaring exchange: %s', exchange_name)
        self._channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=self.EXCHANGE_TYPE)
        print('Exchange declared: %s', self.EXCHANGE)

        # self.setup_queue(self.QUEUE)
        queue_name = self.QUEUE
        print('Declaring queue %s', queue_name)
        userdata = self._channel.queue_declare(queue=queue_name, durable=True)
        self.num_msgs = userdata.method.message_count

        if self.num_msgs == 0:
            return

        print('Binding %s to %s with %s', self.EXCHANGE, queue_name,
              self.ROUTING_KEY)
        self._channel.queue_bind(
            queue_name,
            self.EXCHANGE,
            routing_key=self.ROUTING_KEY)

        print('Queue bound: %s', queue_name)
        self._channel.basic_qos(
            prefetch_count=self._prefetch_count)
        print('QOS set to: %d', self._prefetch_count)

        self._consumer_tag = self._channel.basic_consume(
            self.QUEUE, self.on_message)
        self.was_consuming = True
        self._consuming = True
        self._channel.start_consuming()

    def on_message(self, _unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.
        :param pika.channel.Channel _unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param bytes body: The message body
        """
        print('Received message # %s from %s: %s',
              basic_deliver.delivery_tag, properties.app_id, body)

        print(self.obj)
        if self.inst_type == "channel" or self.inst_type == "course" or self.inst_type == "doubt":
            posts = self.obj.posts
        elif self.inst_type == "topic":
            posts = self.obj.opps
        print("reached ch.posts")
        mcount = Message.query.filter_by(type=self.inst_type).count()
        msg_body = str(body)
        msg_body = msg_body[3:-2]
        msg_lines = msg_body.split('~')
        print(msg_lines)
        sndr = msg_lines[0]
        timest = msg_lines[1]
        print(timest)
        timestamp_ = datetime.strptime(timest, "%Y-%m-%d %H:%M:%S.%f")
        contnt = msg_lines[2]
        mid = self.inst_type + str(mcount)
        msg = Message(msg_id=mid, name=self.QUEUE, sender=sndr, content=contnt, timestamp=timestamp_,
                      type=self.inst_type, replies=[], tags=[])
        posts.append(msg)

        if self.inst_type == "channel" or self.inst_type == "course":
            self.obj.posts = posts
            flag_modified(self.obj, "posts")
        elif self.inst_type == "topic":
            self.obj.opps = posts
            flag_modified(self.obj, "opps")

        print("flag modified")
        db.session.merge(self.obj)
        db.session.flush()
        db.session.commit()
        self.acknowledge_message(basic_deliver.delivery_tag)
        self.num_msgs -= 1
        if (self.num_msgs == 0):
            self._connection.close()

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.
        :param int delivery_tag: The delivery tag from the Basic.Deliver frame
        """
        print('Acknowledging message %s', delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def run(self, obj):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.
        """
        self.obj = obj
        self.connect()
        # self._connection.ioloop.start()


def main():
    # logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
    consumer = ExampleConsumer(amqp_url, "machine-learning")
    consumer.run()


if __name__ == '__main__':
    main()
