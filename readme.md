testing the speed of making a qdrant db when running on the local machine. This test is done by loading all of the functions in a given project into the vectordb
```
❯ python .\testone.py
Loading Encoder
Creating in-memory Qdrant instance
Getting Project Data For 'xyz'
Time taken: 0.35 seconds
Got [3825] Functions.
Creating Collection
Vectorizing Content and Uploading to Qdrant
Time taken: 278.09 seconds
Search:_
```