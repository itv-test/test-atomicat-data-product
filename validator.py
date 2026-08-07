import os
import re
import sys

# Get component type and set Component naming pattern
# COMPONENT_TYPE = os.environ["GHA_PRODUCT_TYPE"]
component_naming_pattern = re.compile("^([a-z]+-?)+")

# Get env vars
DP_NAME = os.environ["GHA_PRODUCT_NAME"].lower()
# BUSINESS_ACCOUNT = os.environ["GHA_BUSINESS_ACCOUNT"]
DOMAIN = os.environ["GHA_DOMAIN"]
PLATFORM = os.environ["GHA_PLATFORM"]

# Check product name ends with valid suffix
# if DP_NAME.endswith(("-data-product", "-data-service")):
#     print(f"Success: Name of data product ({DP_NAME}) contains valid suffix")
# else:
#     print(
#         f"Error: Name of data product ({DP_NAME}) does not contain a valid suffix. Valid suffixes are: '-data-product' or '-data-service'"
#     )
#     sys.exit(1)

# Check length and exit code if > 41 chars
if len(DP_NAME) > 41:
    print(
        f"Error: Name of data product ({DP_NAME}) is too long, shorten to 41 characters or less"
    )
    sys.exit(1)
else:
    print(
        f"Success: Name of data product ({DP_NAME}) meets character length requirement"
    )
    pass

# Check name matches required pattern
if not component_naming_pattern.fullmatch(DP_NAME):
    print(
        f"Error: The Data {DP_NAME} name must match {component_naming_pattern.pattern}, please rename"
    )
    sys.exit(1)
else:
    print(
        f"Success: Name of data product ({DP_NAME}) matches the required naming pattern"
    )
    pass

# validate bartex/crash or crash/bartex
if PLATFORM == "bartex" and DOMAIN != "crash":
    print(
        f"Error: Platform 'bartex' only supports the 'crash' domain "
        f"(got '{DOMAIN}')"
    )
    sys.exit(1)

elif DOMAIN == "crash" and PLATFORM != "bartex":
    print(
        f"Error: Domain 'crash' is only valid for platform 'bartex' "
        f"(got '{PLATFORM}')"
    )
    sys.exit(1)

else:
    print(
        f"Success: Domain '{DOMAIN}' is valid for platform '{PLATFORM}'"
    )
    pass

# Check provided business account is one of existing valid bsuiness accounts for the requested domain
# valid_domains_and_accounts = {
#     "viewer": ["Not Applicable"],
#     "marketing": ["Not Applicable"],
#     "commercial": ["Not Applicable"],
#     "audiences": [
#         "bpr",
#         "finance",
#         "content",
#         "publication",
#         "operational",
#         "insights",
#         "racs",
#     ],
#     "bar": ["Not Applicable"],
#     "dataplatform": ["Not Applicable"],
# }
# valid_business_accounts = valid_domains_and_accounts[DOMAIN]
#
# if BUSINESS_ACCOUNT not in valid_business_accounts:
#     print(
#         f"Error: The requested business account ({BUSINESS_ACCOUNT}) does not exist in {DOMAIN}. Valid business accounts per domain are: {valid_domains_and_accounts}"
#     )
#     sys.exit(1)
# else:
#     print(
#         f"Success: The requested business account ({BUSINESS_ACCOUNT}) exists in {DOMAIN}"
#     )
#     pass
