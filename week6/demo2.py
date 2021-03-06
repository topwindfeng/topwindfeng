import sys
import findspark
findspark.init('/home/topwind/Desktop/spark-2.3.0-bin-hadoop2.7')
from pyspark import SparkContext

if __name__ == "__main__":
    file = sys.argv[1] #raw train file

    sc = SparkContext(appName="demo2")
    data = sc.textFile(file).flatMap(lambda line: line.upper().split(' ')).distinct()
    data.saveAsTextFile("demo2_output8")
    sc.stop()
