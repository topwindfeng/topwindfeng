import sys
import findspark
findspark.init('/home/topwind/Desktop/spark-2.3.0-bin-hadoop2.7')
from pyspark import SparkContext
#MARK file- SUCCESS
if __name__ == "__main__":
    file = sys.argv[1] #raw train file
    sc = SparkContext(appName="demo0")
    data_uc = sc.textFile(file).map(lambda line: line.upper())
    data_uc.saveAsTextFile("demo_upper_output10")

    sc.stop()
