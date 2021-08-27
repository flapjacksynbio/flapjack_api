---
title: API Reference

language_tabs: # must be one of https://git.io/vQNgJ
  - shell
  - python
  - javascript

toc_footers:
  - <a href='http://flapjack.rudge-lab.org/'>Sign Up to Flapjack</a>
  - <a href='https://github.com/slatedocs/slate'>Documentation Powered by Slate</a>

includes:
  #- errors

search: true

code_clipboard: true
---

# Introduction

Flapjack is a data management and analysis tool for genetic circuit design. The system is implemented as a web app with a backend data registry and analysis engine accessible as a REST API. This API is fully documented in the following [GitHub Repository](https://github.com/SynBioUC/flapjack_api), and also we have developed a python package for easier access to the Flapjack API, this package is available in it's [GitHub Repository](https://github.com/SynBioUC/flapjack) and you can see the documentation in the following [web page](https://synbiouc.github.io/flapjack/).

# Authentication

## Register
> To register in Flapjack, use this code:


```python
import requests

url = "http://localhost:8000/api/auth/register/"

payload = "{\n\t\"username\": \"JohnDoe\",\n\t\"password\": \"asd123\",\t\n\t\"password2\": \"asd123\",\n\t\"email\": \"john@doe.com\"\n}\n"
headers = {}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

```

```shell
# With shell, you can just pass the correct header with each request
curl --location --request POST 'http://localhost:8000/api/auth/register/' \
--data-raw '{
		"username": "JohnDoe",
		"password": "asd123",   
		"password2": "asd123",
		"email": "john@doe.com"
```

```javascript
var settings = {
	"url": "http://localhost:8000/api/auth/register/",
	"method": "POST",
	"timeout": 0,
	"data": "{\n\t\"username\": \"JohnDoe\",\n\t\"password\": \"asd123\",\t\n\t\"password2\": \"asd123\",\n\t\"email\": \"john@doe.com\"\n}\n",
};
 
$.ajax(settings).done(function (response) {
	console.log(response);
});
```



This API counts with the facility of a direct registry method.
Required parameters:

`username: JohnDoe`

`password: asd123`

`password2: asd123`

`email: john@doe.com`

## Log In
```python

import requests
 
url = "http://localhost:8000/api/auth/log_in/"
 
payload = "{\n\t\"username\": \"JohnDoe\",\n\t\"password\": \"asd123\"\n}\n"
headers = {}
 
response = requests.request("POST", url, headers=headers, data=payload)
 
print(response.text)

```

```shell
curl --location --request POST 'http://localhost:8000/api/auth/log_in/' \
--data-raw '{
	"username": "JohnDoe",
	"password": "asd123"
}
'
```

```javascript

var settings = {
	"url": "http://localhost:8000/api/auth/log_in/",
	"method": "POST",
	"timeout": 0,
	"data": "{\n\t\"username\": \"JohnDoe\",\n\t\"password\": \"asd123\"\n}\n",
};

$.ajax(settings).done(function (response) {
	console.log(response);
});

```
If you have already registerd as an user you can just log in using the API.

Required parameters:

`username: JohnDoe`


`password: asd123`
## Refresh
```python
import requests
import json
url = "http://localhost:8000/api/auth/refresh/"
refresh_token = ##obtained from the log_in request

refresh = requests.post (
	url,
	data = {'refresh' : refresh_token}
)
## and now the access token is:
refresh.json["access"]
```
In order to refresh the database of the Flapjack API you need to get a refresh token from the log in request.

# Registry

> In order to register data you should have to be loged in using the API.


```python

import requests
model = ## your desire model.
url = f'http://localhost:8000/api/{model}/'
access_token = ## given by the log in request.
kwargs = ## parameters of the model.
Id = ### The ID of the data that you want to delete or patch.

### To post data
response = requests.post(
	url,
	headers = {'Authorization' : 'Bearer ' + str(access_token)},
	data = kwards
)

### To get data
info = requests.get(
	url, 
	headers = {'Authorization' : 'Bearer ' + str(acces_token)},
	data = kwargs
)
### To patch data
patch = requests.patch(
	url+f'{id}/',
	headers= {'Authorization' : 'Bearer ' + str(access_token)},
	data=kwargs
)

### To delete data

delete = requests.delete(
	url+f'{Id}/',
	headers = {'Authorization' : 'Bearer ' + str(access_token)}
)
```

The regestry endpoint contains a way to upload and obtain data using the Flapjack REST API. As a way to further explain how this endpoint works firlty we are going to show the base code to contact the REST API, and in the next subsection we will explain the different models where you can upload and retrieve data.

When you do a post request to the Flapjack API, you will upload your data into de database. On other hand, when you do a get request to the Flapjack API you will be filtering the actual data and returning those models that match the filter criteria. The delete request delete a certain data from the database by the id of the model that you post. And finally, patch is used to update the data of a certain model posted in Flapjack.


## Study

This corresponds to a project, for example a paper or report, that corresponds to a certain question a researcher wants to address.
### Query parameters

Key|Description
---|---
name| Refers to the name given to the study
description | The description of the Study
doi| The doi of the study
owner | The owner of the study
public | Boolean that indicates whether the study is public or private



## Assays 


The assays refears to measurement of experiments, including replicates and varying experimental conditions, performed to explore different aspects of the study.


### Query Parameters

Key|Description
---|---
study | Name of the associated study
id| ID given to the assay
Temperature| Temperature of development of the assay
machine | Machine used for the assay
study| Number of the assay in an specific study


## DNA

DNA corresponds to the DNA parts that, later on, will compose a vector that can be used in the assay.

### Query Parameters

Key|Description
---|---
owner| Owner of the DNA 
name| Name of the DNA 
sboluri| SBOLURI of the DNA 

## Vector

The vector describes the synthetic DNAs encoding a genetic circuit, including links to part composition and sequence via the corresponding SynBioHub URIs.

### Query Parameters

Key|Description
---|---
owner | Name of the owner of the data of the query
name | Name of the vector 
dnas | DNAs conteined in the vector 

## Media

The media corresponds to the composition of the substrate that drives the genetic circuit, media in the case of live cell assays, or extract for cell-free experiments.


### Query Parameters

Key | Description
--- | ---
owner | owner of the media
name | Name of the media
description | Description of the media


## Strain

The strains refers to the chassis organism, if any, hosting the genetic circuit.

### Query Parameters

Key |description
---|---
owner | Name of the owner of the data of the strain
name | Name of the strain
description | Description of the strain

## Chemical

This registry refers to the chemical(s) that compose the supplement used during the experiments used to obtain data.

### Query Parameters
Key|Description
---|---
owner | Name of the owner of the chemical data
name| Name of the chemical
description | Description of the chemical
pubchemid | Pubchem id of the chemical


## Supplement

Supplemente is any supplementary chemicals that interact with components of the genetic circuit. It's compose of a serie of Chemical data objects.

### Query Parameters
Key | Description
---| ---
owner | Name of the owner of the data 
name | Name of the certiain suplement
chemical | Chemicals used in the suplement
concentration | Concentration of the chemicals (Is the concentration of the chemicals or suplement???)

## Sample

Sample orresponds to the basic unit that is subject to measurement, for example a colony or a well in a microplate.

### Query Parameters

Key| Description
---|---
assay | Assays used in the sample
media | Media used in the sample
strain | Strain utilised in the sample
vector | Vector that was used in the sample
supplements | Supplement utilised in the sample
row | ???
col | ???

## Signal

Signal is the subject of measurements, for example a fluorescence channel with given filter bandwidths.

### Query Parameters

Key | Description
--- | ---
owner | Owner of the signal data
name | Name of the signal data
description | Description of the signal data
color | Color of the signal utilized

## Measurement

The messurement is the value of the raw measurement recorded for a particular sample during an assay at a particular time.

### Query Parameters

Key| Description
---|---
sample | Sample that is associated with this measurement
signal | Signal associated with this measurement
value | Value of the measurement
time | Time measurement

# Example of the workflow (REST API)

Now we are going to exemplify how the workflow of the Flapjack REST API works.
## Registry

```python
import requests

url= "http://localhost:8000/api/auth/register/"

payload = {
	"username"="flapjack_test1",
	"password"="flapjack_test2",
	"password2"="flapjack_test2",
	"email"="flapjack_test@test.com"
}
headers = {}
response = requests.post(url, headers = headers, data= payload)
```

Firstly we have to register to Flapjack. For this you have to create your credentials, especificaly the `username`, `password` (you have to repeat it in order to comfirme it), and `email`.


## Log in
```python
import requests

url = "http://localhost:8000/api/auth/log_in/"

payload = {
	"username":"flapjack_test1",
	"password":"flapjack_test2"
}
headers = {}
response = requests.post(
	url,
	headers = headers, 
	data= payload
)
```

If you are already registered in Flapjack you can log in to it using your `username` and `password`.
## Upload data

```python 
import requests
import json 

url = "http://localhost:8000/api/"
## Firstly we have to log in 
login = {
	"username": "flapjack_test1",
	"password": "flapjack_test2"
}

headers={}

log_in = requests.post(
	url+"auth/log_in/", 
	headers= headers, 
	data=login
).json()
## After this you have to refresh

refresh_token = log_in['refresh']

refresh = requests.post(
	url + "auth/refresh/", 
	data = {"refresh" : refresh_token}
).json()
## Now we can upload our data to the server

access_token=log_in["access"]
model = "study"
kwargs={
	"name":"test-study1",
	"description":"This is an study to test the Flapjack REST API",
	"owner":"flapjack_test1",
	"public":False
}
post= requests.post(
	url+f'{model}/',
	headers={"Authorization": 'Bearer ' + access_token},
	data = kwargs
)
```
> The repsonse to the post requests is the following
```json
[
	{
		'id': 3, 
		'is_owner': True, 
		'shared_with': [], 
		'name': 'test-study', 
		'description': 'This is an study to test the Flapjack REST API', 
		'doi': '', 
		'public': False
	}
]
```
Now imagine that you want to upload an study based with the following parameters:
`Name: test-study1`
`Description: This is a study to test the Flapjack REST API.`
`owner: flapjack_test1`
`Public: False`

To do this you need to post this data to the Flapjack REST API. The code to do this is in the right section.

## Get Data
```python
import requests
import json

url = "http://localhost:8000/api/"
## Firstly we have to log in 
login = {
	"username": "flapjack_test1",
	"password": "flapjack_test2"
}

headers={}

log_in = requests.post(
	url+"auth/log_in/", 
	headers= headers, 
	data=login
).json()
## After this you have to refresh

refresh_token = log_in['refresh']

refresh = requests.post(
	url + "auth/refresh/", 
	data = {"refresh" : refresh_token}
).json()

## Assuming that you have uploaded a study previously

access_token=log_in["access"]
model = "study"
kwargs={
	"name":"test-study1",
	"description":"This is an study to test the Flapjack REST API",
	"owner":"flapjack_test1",
	"public":False
}
get = requests.post(
	url+f'{model}/',
	headers={"Authorization": 'Bearer ' + access_token},
	data = kwargs
)

```

Now as we upload data to Flapjack we can also get data from the database of Flapjack. In order to do this we need to follow up the following workflow.


For more examples you can visit our [GitHub repository](https://github.com/SynBioUC/flapjack_api).
# Analysis
>To connect to the websocket

```python
import websockets
import json

params = kwargs

uri = 'ws://localhost:8000/ws/analysis/analysis?token='+access_token
payload = {
	"type" : "analysis",
	"parameters" : params
}

with websockets.connect(uri) as websocket:
	websocket.send(json.dumps(payload))
	response_json = webscket.recv()
	response data = json.loads(response_json)
```
This endpoint, unlike the past endopoints, corresponds to a websocket, the analysis is in charge of developing most of the calculations and the result is a .json file that can be interpreted as a pandas data frame. 

The `params` variable refers to the different kinds of analysis and data provided to the analysis websocket.

**Types of analysis**
## Velocity

### Query Parameters

Key | Description
--- | --- 
df | DataFrame containing the data to analyze. 
pre_smoothing |  Savitsky-Golay filter parameter. Is the initial smoothing parameter.
post_smoothing | Savitsky-Golay filter parameter. Is the final smoothing parameter.

## Expression Rate (Indirect)

The expression rate analysis refers to analyze the expression of the genes in a certain study. In this case, the analysis is done using an indirect method.

### Query Parameters

Key | Description
--- | ---
df | DataFrame containing the data to analyze. 
density_df | DataFrame with density measurements.
pre_smoothing | Savitsky-Golay filter parameter. Is the initial smoothing parameter.
post_smoothing | Savitsky-Golay filter parameter. Is the final smoothing parameter.

## Expression Rate (Direct)

This analysis of the expression rate is based on a direct method.

### Query Parameters

Key | Description
---|---
df | DataFrame containing the data to analyze. 
density_df | DataFrame with density (biomass) measurements.
degr | Degradation rate of the reporter protein. 
eps_L | Insignificant value for model fitting. 

## Expression Rate (Inverse)

This expression rate analysis is based on a inverse method.

### Query Parameters

Key | Description
--- | ---
df | DataFrame containing the data to analyze. 
density_df | DataFrame with density (biomass) measurements.
degr | Degradation rate of the reporter protein. 
eps | Tikhoniv regularization parameter.
n_gaussians | Number of gaussians in basis. 

## Mean Expression

This analysis returns a data frame containing the mean values for each sample.

### Query Parameters
Key | Description
--- | ---
df | DataFrame containing the data to analyze. 

## Max expression 

This analysis returns a data frame containing the max values for each sample.

### Query Parameters

Key| Description
---|---
df | DataFrame containing the data to analyze.

## Mean Velocity

This analysis returns a data frame containing the mean velocity for each sample.

### Query Parameters
Key | Description
---|---
df | DataFrame containing the data to analyze.

## Max Velocity

This analysis returns a data frame containing the max velocity for each sample.

### Query Parameters

Key | Description
---|---
df | DataFrame containing the data to analyze.

## Induction Curve
**Is this correct?**
### Query Parameters
Key | Description
---|---
df | DataFrame containing the data to analyze.

## Kymograph
**This one is strange because it calls the past analysis.**
### Query Parameters
Key | Description
---|---
df | DataFrame containing the data to analyze.

## Heatmap 

### Query Parameters

Key | Description
---|---
df | DataFrame containing the data to analyze.

## Ratiometric Alpha

### Query Parameters

Key | Description
---|---
df | DataFrame containing the data to analyze.
bounds | Tuple of list of min and max values for  Gompertz model parameters.
density_df | DataFrame containing biomass measurements.
ndf | Number of doubling times to extend exponential phase.

## Ratiometric Rho

### Query Parameters

Key | Description
---|---
df | DataFrame containing the data to analyze.
bounds | Tuple of list of min and max values for  Gompertz model parameters.
density_df | DataFrame containing biomass measurements.
ref_df | DataFrame containing reference measurements.
ndf | Number of doubling times to extend exponential phase.***

# Plot

Plot is an websocket endopoint of the Flapjack API. This endpoint generates json objects oriented to generate diffent plots (hence its name), this json object can be interpreted by the python package matplotLib.

## Normalize

In order to normalize the data and plot it we have provided many different options.

### Query Parameters

Key | Description
---|---
Temporal Mean | Normalize the data by the temporal mean of the data. 
Mean/std | Normalize the data by the mean of the date divided by the standar deviation.
Min/Max | Normalize the data by the cocient of the minimum and maximum values.
None | The data is not normalized.

## Subplots

When making a plot you can select different subplots according to what best suits your needs. You can plot the different registry parameters.

### Query Parameters

Key | Description
--- | ---
Signal | The subplots are plotted from signal data.
Study | The subplots are plotted from study data.
Assay | The subplots are plotted from assay data.
Vector | The subplots are plotted from vector data.
Media | The subplots are plotted from media data.
Strain | The subplots are plotted from strain data.
Supplemente | The subplots are plotted from supplement data.

## Lines/Markers

This refers to the curves you want to be shown in each of the plots. The query parameters are the same as the previously mentioned.

## Plot

It corresponds to the detail you want to have in each of the curves.

### Query Parameters

Key | Description
--- | ---
Mean | The datail is in the mean of the curves.
Mean +/- std | The detail is in the Mean, max, minimum, and standar deviation of the data.
All data points | You plot all the points, not givin more detail to anyone.