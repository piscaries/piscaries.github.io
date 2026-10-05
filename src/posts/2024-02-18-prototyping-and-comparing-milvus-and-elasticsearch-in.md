---
title: "Prototyping and comparing Milvus and Elasticsearch in standalone mode"
date: 2024-02-18
description: "The tech industry has been exploring vector databases primarily due to the rise and increasing importance of machine learning applications. These technologies rely heavily on…"
original: "https://medium.com/@piscaries/prototyping-and-comparing-milvus-and-elasticsearch-on-standalone-mode-fb4f2a3390ef"
---

![](/images/prototyping-and-comparing-milvus-and-elasticsearch-in/e0f7d0ab79.jpeg)

The tech industry has been exploring vector databases primarily due to the rise and increasing importance of machine learning applications. These technologies rely heavily on vector data for various functionalities, such as recommendation systems, similarity searches, natural language processing, and image recognition.

Among all vector DB solutions, Elasticsearch and Milvus are two popular options. This article will:

1.  **Prototype** indexing and searching on these two popular vector DBs by demonstrating code and setup on standalone nodes
2.  **Compare** these two vector DBs on search result and load test latency
3.  **Share** the author’s perspective on the characteristics and practical applications of vector search.

Note: Large scale on-prem or cloud deployment is beyond this article’s scope.

## The Introduction of Elasticsearch and Milvus

[Elasticsearch](https://www.elastic.co/elasticsearch) is a highly scalable open-source full-text search and analytics engine widely used by the industry. Elastic is the company behind Elasticsearch. While it continues to develop Elasticsearch, the company also provides commercial products.

[Milvus](https://milvus.io/) is an open-source vector database designed by [Zilliz](https://zilliz.com/) specifically for AI and ML applications. It is optimized for storing and searching large-scale vector data.

Before delving into the prototype of indexing and performance comparison, there are a few differences worth attention between these two Vector DBs:

1.  Full text search: it means to directly apply keyword text but not vector for document searching. Elasticsearch started from text search, so it supports text search. Milvus is built for high-performing vector search, so it does not support full text search.
2.  Maturity: Elasticsearch offers a wide range of tools such as Kibana for visualization and Logstash for log processing. Milvus is newer to the market, so the community support is not as extensive as Elasticsearch yet.
3.  License: Milvus is under Apache 2.0, so it is free to be used, modified and distributed. The machine learning features are free to use. Elasticsearch changed its License in 2021 from Apache License 2.0 to a combination of Server Side Public License and Elastic License. Many machine learning features are under paid license. (I encountered some limitations in my exploration but worked with turnaround solutions)

## Prerequisite

**Data **: [Kaggle Book Dataset](https://www.kaggle.com/datasets/saurabhbagchi/books-dataset/data). I used it for [my previous blog](https://medium.com/@piscaries/large-language-model-finetuning-practice-7e131291046e) on LLM finetuning. I will continue to use it for this article. I extracted 5000 books for indexing. The data can be found on my Github [repo](https://github.com/piscaries/vectordbdemos/blob/main/data/books_5000.csv). I concatenate title, author, publisher and year fields together to build the vector indexing field because these fields are short and combining them together can enable us search multiple field information about books.

**Setup **: I set up Milvus and Elasticsearch Docker nodes in standalone mode on my workstation. For load testing, I also used Docker with the load testing tool Locust.

## Setup Milvus and Index data

To run Milvus on Docker, you can refer to the docker-compose.yml file in my code [repo](https://github.com/piscaries/vectordbdemos/blob/main/milvus/docker-compose.yml).

I used pymilvus on my Jupyter notebook. The script is also shared in the code [repo](https://github.com/piscaries/vectordbdemos/blob/main/milvus/milvus_books_vector_on_merged.py).

1.  Connect to Milvus

``` graf
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

connections.connect(host='<milvus hostname>', port='19530')
```

2\. Create a Collection

``` graf
def create_milvus_collection(collection_name, dim=768):
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)
    
    fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=20),
            FieldSchema(name="book_title", dtype=DataType.VARCHAR, max_length=500), 
            FieldSchema(name="book_author", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="year_of_publication", dtype=DataType.VARCHAR, max_length=10),
            FieldSchema(name="publisher", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="combined_fields", dtype=DataType.VARCHAR, max_length=710),
            FieldSchema(name="combined_fields_vector", dtype=DataType.FLOAT_VECTOR,dim=dim)
    ]
    schema = CollectionSchema(fields=fields, description='Book-Info')
    collection = Collection(name=collection_name, schema=schema)
    
    index_params = {
        'metric_type': "COSINE",
        'index_type': "IVF_SQ8",
        'params': {"nlist": 1}
    }
    collection.create_index(field_name='combined_fields_vector', index_params=index_params)
    return collection

collection = create_milvus_collection('book_search')
```

“combined_fields_vector” is the field to be indexed as the float vector. nlist is set as 1 because this prototyping only has 5000 documents. Thus, we only have one index cluster so all indexed documents will be scanned when searching. Metric_type is set to COSINE. This should be consistent with Elasticsearch setup so we can get close to an “apple-to-apple” comparison.

3\. Insert data with [towhee](https://github.com/towhee-io/towhee?tab=readme-ov-file)

``` graf
from towhee import ops, pipe
import numpy as np

insert_pipe = (pipe.input('id', 'book_title', 'book_author', 'year_of_publication', 'publisher', 'combined_fields') 
               .map('combined_fields', 'combined_fields_vector', ops.text_embedding.dpr(model_name='facebook/dpr-ctx_encoder-single-nq-base'))
               .map('combined_fields_vector', 'combined_fields_vector', lambda x: x / np.linalg.norm(x, axis=0))
               .map(('id', 'book_title', 'book_author', 'year_of_publication', 'publisher', 'combined_fields', 'combined_fields_vector'), 'res', ops.ann_insert.milvus_client(host='milvus-standalone', port='19530', collection_name='book_search'))
               .output('res') )

import csv
with open('path to books_5000.csv', encoding='Latin-1') as f:
    reader = csv.reader(f, delimiter=';')
    next(reader)
    for row in reader:
        row = row[0:5]
        row.append(row[1] + " " + row[2] + " " + row[3] + " " + row[4])
        insert_pipe(*row)
```

It took 240s (repeated a few times). However, I feel it shouldn’t take that long. It could be some unrelated configuration issue.

4\. Search the collection

``` graf
encoder = ops.text_embedding.dpr(model_name="facebook/dpr-ctx_encoder-single-nq-base")
collection.load()

search_params = {
    "metric_type": "COSINE", 
    "offset": 0, 
    "ignore_growing": False, 
    "params": {"nprobe": 1}
}

results = collection.search(
    data=[encoder(<text query>)], 
    anns_field="combined_fields_vector", 
    param=search_params,
    limit=20,
    expr=None,
    output_fields=['book_title', 'book_author', 'year_of_publication', 'publisher'],
    consistency_level="Strong"
)
```

Returns 20 closed results to \<text query\> based on vector cosine similarity.

5\. Done

## Setup Elasticsearch and Index data

To run Elasticsearch on Docker, you can refer to the docker-compose.yml file in my code [repo](https://github.com/piscaries/vectordbdemos/blob/main/elasticsearch/docker-compose.yml). It runs in standalone mode and disables security features.

I shared Jupyter script in the code [repo](https://github.com/piscaries/vectordbdemos/blob/main/elasticsearch/elasticsearch_books.py).

1.  Connect to Elasticsearch

``` graf
from elasticsearch import Elasticsearch

client = Elasticsearch(
    "http://<elastic search hostname>:9200"
)
```

2\. Create an index

``` graf
# Define the mapping
mappings = {
    "properties": {
        "book_vector": {
            "type": "dense_vector",
            "dims": 768,
            "index": "true",
            "similarity": "cosine"
        }
    }
}
# Create the index
client.indices.create(index='book_index', mappings=mappings)
```

3\. Index data

``` graf
from sentence_transformers import SentenceTransformer
from urllib.request import urlopen
import csv
import json

model = SentenceTransformer('sentence-transformers/facebook-dpr-ctx_encoder-single-nq-base')
operations = []
with open('path to books_5000.csv', encoding='Latin-1') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        operations.append({"index": {"_index": "book_index"}})
        combined_book_fields = row["Book-Title"] + " " + row["Book-Author"] + " " + row["Year-Of-Publication"] + " " + row["Publisher"]
        row["book_vector"] = model.encode(combined_book_fields).tolist()
        operations.append(row)

client.bulk(index="book_index", operations=operations, refresh=True)
```

It took around 60s to build the index (Repeated a few times)

4\. Search

``` graf
response = client.search(
    index="book_index",
    knn={
      "field": "book_vector",
      "query_vector": model.encode(<text query>),
      "k": 20,
      "num_candidates": 5000,
    },
    size=50
)
```

Returns 20 closed results to \<text query\> based on vector cosine similarity.

5\. Done

## Search quality analysis on example queries

The purpose of this analysis is to help us get a taste on what we can benefit or lose by using vector search.

**Setup**:

A. I created a few query examples by using book titles, authors, years of publishing and publishers. I also created a few natural language questions, such as “What books did O’Reilly publish”.

B.I set the num of results to 20 and calculated Precision and Recall.

C. Performed on both Milvus and Elasticsearch. Results are shared in the code repo\[[Milvus](https://github.com/piscaries/vectordbdemos/blob/main/data/vector%20search%20result%20-%20Milvus.csv), [Elasticsearch](https://github.com/piscaries/vectordbdemos/blob/main/data/vector%20search%20result%20-%20ElasticSearch.csv)\].

**Result**:

1.  The results of Milvus and Elasticsearch show lots of similarity after we use the same embedding model and similarity metric. It is a cross validation of their implementations.
2.  Overall precision and recall are believed to be lower than text search.
3.  Vector search is not semantic search. It cannot understand human questions such as “What books did O’Reilly publish”. The result is worse than purely query with “O’Reilly”
4.  Vector search can help discovery similar concepts. E.g., for the query “The Future Just Happened”, vector search found a few books conceptually close but not sharing common query keywords, such as “ From This Moment on”, “The Coming” .

**Potential improvement**:

1.  The search quality is highly related to the embedding model. Understanding the embedding model for the search problem is important.
2.  Index each individual fields and create multiple vector indexes for the data.
3.  Combine text search and leverage semantic search techniques such as query understanding or LLM related search technology
4.  Expand retrieval returns and apply ranking models to increase precision and recall at the same time

## Load testing with Locust

I choose [Locust](https://locust.io/) for load testing because of the limitation of Elasticsearch support on vector search. Elasticsearch enables curl http request with vector, but calling an embedding model in curl requires commercial license. However, Elasticsearch python connection allows calling an embedding model in search. So an easy turnaround solution is to find a python load testing tool.

I will skip the [instruction](https://docs.locust.io/en/stable/) of Locust. If you want a standalone Locust Docker-compose.yml file, you can find in my [repo](https://github.com/piscaries/vectordbdemos/blob/main/locust/docker-compose.yml). Meanwhile, you can also find the locustfile.py files that I used to test the two DBs in the code repo\[[Milvus](https://github.com/piscaries/vectordbdemos/blob/main/locust/locustfile_milvus.py), [Elasticsearch](https://github.com/piscaries/vectordbdemos/blob/main/locust/locustfile_es.py)\].

I performed two rounds of load test separately on the two DBs without changing machine context. One test simulates 20 users and the other simulates 30 users. The user number is small due to my Docker engine memory limit, but we don’t need a comprehensive test here.

**Result**: The response time from Milvus is significantly better than Elasticsearch based on my machine setup. Milvus is 15% better on average response time than Elasticsearch and 20% better on TP95 than Elasticsearch.

**Note**: Since my setup are just two standalone Docker nodes on my workstation, the conclusion cannot be applied to other scenarios such as distributed mode or cloud environment. I would be happy to take a look for those scenarios if needed.

## What to choose

Both vector DBs provides methods for creating indexes, performing nearest neighbor searches. Milvus focuses on optimizing vector search. In my opinion, it really depends on the application’s situation and available resources:

- If the use case heavily depends on vector search, such as image, audio or video search. Milvus could be a better choice in my opinion.
- If the application has been built on Elasticsearch already, leveraging Elasticsearch vector search could be a good start. Whether to purchase a commercial license is another topic, but it shouldn’t be difficult to implement some licensed ML features such as KNN search, embedding model integration, and blended search on text and vector results.
- Maintaining two types of DBs at the same time could be useful, but it should be a trade-off together with business impact and other potential ML areas worth investment such as ranking and query understanding.

## Summary

1.  This article did preliminary comparison on Elasticsearch and Milvus, two of the popular vector DB solutions. It provided prototyping for a quick vector DB understanding and shares [code](https://github.com/piscaries/vectordbdemos/tree/main) for anyone who wants to play with it.
2.  The search results of the two vector DBs on the given dataset are comparable.
3.  In terms of latency, Milvus outperforms Elasticsearch on standalone nodes.

Let me know if you have any questions or need any help to build search solutions. If you want to refer any part of this article, please add reference to this article’s link.

## References

1.  Milvus: [https://milvus.io/docs/overview.md](https://milvus.io/docs/overview.md)
2.  Elasticsearch: [https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
3.  Locust: [https://docs.locust.io/en/stable/](https://docs.locust.io/en/stable/)
