# Salesforce Data Cloud Setup For PyDCMem

Since we are using Salesforce Data Cloud as the backend for Data processing and storage, we assume that a Data Cloud instance has been setup within your Salesforce Org. If you are unsure of Data Cloud [here](https://help.salesforce.com/s/articleView?id=data.c360_a_setup_provision.htm&type=5) Data Cloud setup guide.

Now, let's set up the Data Cloud based write and read path for PyDCMem.

### Write Path: Streaming Ingestion Setup
PyDCMem uses [DC Ingestion API](https://developer.salesforce.com/docs/data/data-cloud-int/references/data-cloud-ingestionapi-ref/c360-a-api-get-started.html) to write data into Data Cloud.

The setup process is standard, but when you set up Ingestion API connector use the [AIUserAttributesSchema.yml](src/AIUserAttributesSchema.yml) file. This will create the Ingestion connector specifically for this object.

Once you have the connector setup head over to the Data Cloud App, and create the corresponding DataStream, DataLake and DataModel objects for the stream you created above.

Here are some useful resources:
- video [demonstration](https://www.youtube.com/watch?v=3xWSVGcTORI) of how to set-up Salesforce Data Cloud Ingestion API
- [comprehensive video over some Data Cloud basics and Ingestion API](https://www.youtube.com/watch?v=usfUhzq5kl0)
- Help [Guide](https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-create-ingestion-data-stream.html)

NOTES: 
- you can name the connector and the objects anything you want, but you will need to provide those values env. variables mentioned below.
- before setting up Ingestion API, you will need to set up a connected app for OAuth JWT Bearer in your Salesforce Org, and that is also covered in the above videos. This connected app is required for the data read path as well. If you need to more details on Salesforce connected apps, you can refer to this [blogpost](https://medium.com/@immvbhonsle/salesforce-connected-apps-and-oauth-tokens-729badb30370)  

### Read Path: Search Index Pipeline Setup

PyDCMem use Data Cloud's [SQL Query API](https://developer.salesforce.com/docs/data/data-cloud-query-guide/guide/dc-sql-query-apis.html) to read data from Data Cloud. This data is read for the following purposes:
- fetching relevant user attributes to the given utterance
- fetching relevant user attributes for semantic similarity during a memory update operation

PyDCMem exclusively queries the following three object from Data Cloud via the SQL Query API:

- AIUserAttributes__dlm: the main memory table
- AIUserAttributes_chunk__dlm: Memory chunk object
- AIUserAttributes_index__dlm: Memory vector index object

The first object is created when you set up the Streaming Ingestion Path above. The next two objects are auto created when you set up the Search Index pipeline (details below) 

NOTE: the above names may change, depending on how you name your objects.

Since our primary purpose of reading data into PyDCMem is to find relevant attributes, we need a relevancy search pipeline in Data Cloud, this is exactly what we get with Data Cloud [Search Index Pipeline](https://help.salesforce.com/s/articleView?id=data.c360_a_search_index_ground_ai.htm&type=5). The following video walks through the corresponding Search Index Pipeline setup:

[Search_Index_Setup.mov](..%2Fresources%2FSearch_Index_Setup.mov)