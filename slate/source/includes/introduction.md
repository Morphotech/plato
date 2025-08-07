# Introduction

Welcome to Plato! Plato is a 
[REST API](https://en.wikipedia.org/wiki/Representational_state_transfer) that provides developers with a 
simple-to-use interface for templating. 

In a very summarized flow, you create your own HTML templates, adding placeholders that are later filled with specific 
data, then you define the data the template requires via a JSON schema structure; after adding the template to your
Plato instance, specific endpoints can be used to render the template in various formats with the provided data.

As an example, Plato can be used to define and render custom HTML emails.

Every endpoint available on Plato is described and accompanied by a visual example of how the API responds.
For an improved experience when integrating Plato to your code, you can import our libraries:

- Python: <a href="https://pypi.org/project/plato-helper-py/">plato-helper-py</a> on PyPi
- Java: <a href="TBD">plato-helper-java</a> on Nexus TODO Link

All Python examples used in the examples are from the above library. 

When executing the Plato API, a Swagger page is provided, which can be used for testing or to get more information about
the endpoints. Locally, it is hosted on [http://localhost/docs/](http://localhost/docs/). If you are 
using our Docker image, you can host it on any port. You can also use the Bruno Collection supplied in the repository 
to test the API endpoints.

Please check our [Privacy Policy](https://vizidox.com/privacypolicy) for more details on data collection. Furthermore, by using 
the Core API you are agreeing to our [Terms and Conditions](https://vizidox-shared-files.s3.eu-west-2.amazonaws.com/terms_conditions/Terms+of+Use+Vizidox.html).
