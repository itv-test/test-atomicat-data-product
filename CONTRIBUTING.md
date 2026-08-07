# Steps to configure and deploy a data product

## Infrastucture

Before deploying the data product make sure that the data product is added to cortex first.

### Add the Data Product to Cortex/Bartex

1. Clone either cortex-data-platform bartex-data-platform repositories and add the
data product name to /global_config/data_products.yml on a new branch

example:
```
your-data-product:
  domain: commercial
  github_repo: your-data-product
```
2. Request Data Platform to merge your change.

3. Once your branch has been merged open the github UI for your data product repository and click on `Actions` 

4. Select the `Apply Data Product Setup` action from the left hand menu and select the environment for deployment. Run the workflow and wait till it completes successfully

### Deploy your Data Product

1. Open the github repostory UI for your Data Product and click on `Actions` (Github Actions).

2. Select the `Deploy` action from the left hand menu and select the environment for deployment. Override the image tag if you wish to deploy a new image, or override the `main` branch if you wish to test another branch.

3. Run the workflow and wait for it to complete successfully.

## Terraform Examples
The following are terraform module examples pulled directly from the latest module README's

<!-- BEGIN EXAMPLE -->



<!-- END EXAMPLE -->
