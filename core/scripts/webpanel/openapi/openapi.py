from fastapi import FastAPI

from config import CONFIGS


def setup_openapi_schema(app: FastAPI):
    """Set up the OpenAPI schema for the API.

    The OpenAPI schema is modified to include the API key in the
    "Authorization" header. All routes under /api/v1/ are modified to
    require the API key.
    """

    app.openapi_schema = app.openapi()

    app.openapi_schema["servers"] = [
        {
            "url": f"/{CONFIGS.ROOT_PATH}",
            "description": "Root path of the API"
        }
    ]

    # Define API key in the OpenAPI schema
    # It's a header with the name "Authorization"
    app.openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization"
        }
    }

    # Apply the API key requirement to all paths under /api/v1/ dynamically
    for path, operations in app.openapi_schema["paths"].items():
        if path.startswith("/api/v1/"):  # Apply security to routes starting with /api/v1/
            for operation in operations.values():
                if "security" not in operation:
                    operation["security"] = []
                operation["security"].append({"ApiKeyAuth": []})
