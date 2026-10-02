# Response - Change Status Code - FastAPI

Source: https://fastapi.tiangolo.com/advanced/response-change-status-code/

# Response - Change Status Code[¶](https://fastapi.tiangolo.com/advanced/response-change-status-code/#response-change-status-code "Permanent link")
You probably read before that you can set a default [Response Status Code](https://fastapi.tiangolo.com/tutorial/response-status-code/).
But in some cases you need to return a different status code than the default.
## Use case[¶](https://fastapi.tiangolo.com/advanced/response-change-status-code/#use-case "Permanent link")
For example, imagine that you want to return an HTTP status code of "OK" `200` by default.
But if the data didn't exist, you want to create it, and return an HTTP status code of "CREATED" `201`.
But you still want to be able to filter and convert the data you return with a `response_model`.
For those cases, you can use a `Response` parameter.
## Use a `Response` parameter[¶](https://fastapi.tiangolo.com/advanced/response-change-status-code/#use-a-response-parameter "Permanent link")
You can declare a parameter of type `Response` in your _path operation function_ (as you can do for cookies and headers).
And then you can set the `status_code` in that _temporary_ response object.
[Python 3.10+](https://fastapi.tiangolo.com/advanced/response-change-status-code/#__tabbed_1_1)

```
from fastapi import FastAPI, Response, status

app = FastAPI()

tasks = {"foo": "Listen to the Bar Fighters"}


@app.put("/get-or-create-task/{task_id}", status_code=200)
def get_or_create_task(task_id: str, response: Response):
    if task_id not in tasks:
        tasks[task_id] = "This didn't exist before"
        response.status_code = status.HTTP_201_CREATED
    return tasks[task_id]

```

And then you can return any object you need, as you normally would (a `dict`, a database model, etc).
And if you declared a `response_model`, it will still be used to filter and convert the object you returned.
**FastAPI** will use that _temporary_ response to extract the status code (also cookies and headers), and will put them in the final response that contains the value you returned, filtered by any `response_model`.
You can also declare the `Response` parameter in dependencies, and set the status code in them. But keep in mind that the last one to be set will win.
