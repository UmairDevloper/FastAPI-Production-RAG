# Status Codes - FastAPI

Source: https://fastapi.tiangolo.com/reference/status/

# Status Codes[¶](https://fastapi.tiangolo.com/reference/status/#status-codes "Permanent link")
You can import the `status` module from `fastapi`:

```
from fastapi import status

```

`status` is provided directly by Starlette.
It contains a group of named constants (variables) with integer status codes.
For example:
  * 200: `status.HTTP_200_OK`
  * 403: `status.HTTP_403_FORBIDDEN`
  * etc.


It can be convenient to quickly access HTTP (and WebSocket) status codes in your app, using autocompletion for the name without having to memorize the integer status codes.
Read more about it in the [FastAPI docs about Response Status Code](https://fastapi.tiangolo.com/tutorial/response-status-code/).
## Example[¶](https://fastapi.tiangolo.com/reference/status/#example "Permanent link")

```
from fastapi import FastAPI, status

app = FastAPI()


@app.get("/items/", status_code=status.HTTP_418_IM_A_TEAPOT)
def read_items():
    return [{"name": "Plumbus"}, {"name": "Portal Gun"}]

```

##  `` fastapi.status [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status "Permanent link")
HTTP codes See HTTP Status Code Registry: https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml
And RFC 9110 - https://www.rfc-editor.org/rfc/rfc9110
###  `` HTTP_100_CONTINUE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_100_CONTINUE "Permanent link")

```
HTTP_100_CONTINUE = 100

```

###  `` HTTP_101_SWITCHING_PROTOCOLS `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_101_SWITCHING_PROTOCOLS "Permanent link")

```
HTTP_101_SWITCHING_PROTOCOLS = 101

```

###  `` HTTP_102_PROCESSING `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_102_PROCESSING "Permanent link")

```
HTTP_102_PROCESSING = 102

```

###  `` HTTP_103_EARLY_HINTS `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_103_EARLY_HINTS "Permanent link")

```
HTTP_103_EARLY_HINTS = 103

```

###  `` HTTP_200_OK `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_200_OK "Permanent link")

```
HTTP_200_OK = 200

```

###  `` HTTP_201_CREATED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_201_CREATED "Permanent link")

```
HTTP_201_CREATED = 201

```

###  `` HTTP_202_ACCEPTED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_202_ACCEPTED "Permanent link")

```
HTTP_202_ACCEPTED = 202

```

###  `` HTTP_203_NON_AUTHORITATIVE_INFORMATION `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_203_NON_AUTHORITATIVE_INFORMATION "Permanent link")

```
HTTP_203_NON_AUTHORITATIVE_INFORMATION = 203

```

###  `` HTTP_204_NO_CONTENT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_204_NO_CONTENT "Permanent link")

```
HTTP_204_NO_CONTENT = 204

```

###  `` HTTP_205_RESET_CONTENT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_205_RESET_CONTENT "Permanent link")

```
HTTP_205_RESET_CONTENT = 205

```

###  `` HTTP_206_PARTIAL_CONTENT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_206_PARTIAL_CONTENT "Permanent link")

```
HTTP_206_PARTIAL_CONTENT = 206

```

###  `` HTTP_207_MULTI_STATUS `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_207_MULTI_STATUS "Permanent link")

```
HTTP_207_MULTI_STATUS = 207

```

###  `` HTTP_208_ALREADY_REPORTED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_208_ALREADY_REPORTED "Permanent link")

```
HTTP_208_ALREADY_REPORTED = 208

```

###  `` HTTP_226_IM_USED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_226_IM_USED "Permanent link")

```
HTTP_226_IM_USED = 226

```

###  `` HTTP_300_MULTIPLE_CHOICES `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_300_MULTIPLE_CHOICES "Permanent link")

```
HTTP_300_MULTIPLE_CHOICES = 300

```

###  `` HTTP_301_MOVED_PERMANENTLY `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_301_MOVED_PERMANENTLY "Permanent link")

```
HTTP_301_MOVED_PERMANENTLY = 301

```

###  `` HTTP_302_FOUND `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_302_FOUND "Permanent link")

```
HTTP_302_FOUND = 302

```

###  `` HTTP_303_SEE_OTHER `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_303_SEE_OTHER "Permanent link")

```
HTTP_303_SEE_OTHER = 303

```

###  `` HTTP_304_NOT_MODIFIED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_304_NOT_MODIFIED "Permanent link")

```
HTTP_304_NOT_MODIFIED = 304

```

###  `` HTTP_305_USE_PROXY `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_305_USE_PROXY "Permanent link")

```
HTTP_305_USE_PROXY = 305

```

###  `` HTTP_306_RESERVED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_306_RESERVED "Permanent link")

```
HTTP_306_RESERVED = 306

```

###  `` HTTP_307_TEMPORARY_REDIRECT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_307_TEMPORARY_REDIRECT "Permanent link")

```
HTTP_307_TEMPORARY_REDIRECT = 307

```

###  `` HTTP_308_PERMANENT_REDIRECT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_308_PERMANENT_REDIRECT "Permanent link")

```
HTTP_308_PERMANENT_REDIRECT = 308

```

###  `` HTTP_400_BAD_REQUEST `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_400_BAD_REQUEST "Permanent link")

```
HTTP_400_BAD_REQUEST = 400

```

###  `` HTTP_401_UNAUTHORIZED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_401_UNAUTHORIZED "Permanent link")

```
HTTP_401_UNAUTHORIZED = 401

```

###  `` HTTP_402_PAYMENT_REQUIRED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_402_PAYMENT_REQUIRED "Permanent link")

```
HTTP_402_PAYMENT_REQUIRED = 402

```

###  `` HTTP_403_FORBIDDEN `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_403_FORBIDDEN "Permanent link")

```
HTTP_403_FORBIDDEN = 403

```

###  `` HTTP_404_NOT_FOUND `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_404_NOT_FOUND "Permanent link")

```
HTTP_404_NOT_FOUND = 404

```

###  `` HTTP_405_METHOD_NOT_ALLOWED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_405_METHOD_NOT_ALLOWED "Permanent link")

```
HTTP_405_METHOD_NOT_ALLOWED = 405

```

###  `` HTTP_406_NOT_ACCEPTABLE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_406_NOT_ACCEPTABLE "Permanent link")

```
HTTP_406_NOT_ACCEPTABLE = 406

```

###  `` HTTP_407_PROXY_AUTHENTICATION_REQUIRED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED "Permanent link")

```
HTTP_407_PROXY_AUTHENTICATION_REQUIRED = 407

```

###  `` HTTP_408_REQUEST_TIMEOUT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_408_REQUEST_TIMEOUT "Permanent link")

```
HTTP_408_REQUEST_TIMEOUT = 408

```

###  `` HTTP_409_CONFLICT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_409_CONFLICT "Permanent link")

```
HTTP_409_CONFLICT = 409

```

###  `` HTTP_410_GONE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_410_GONE "Permanent link")

```
HTTP_410_GONE = 410

```

###  `` HTTP_411_LENGTH_REQUIRED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_411_LENGTH_REQUIRED "Permanent link")

```
HTTP_411_LENGTH_REQUIRED = 411

```

###  `` HTTP_412_PRECONDITION_FAILED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_412_PRECONDITION_FAILED "Permanent link")

```
HTTP_412_PRECONDITION_FAILED = 412

```

###  `` HTTP_413_CONTENT_TOO_LARGE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_413_CONTENT_TOO_LARGE "Permanent link")

```
HTTP_413_CONTENT_TOO_LARGE = 413

```

###  `` HTTP_414_URI_TOO_LONG `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_414_URI_TOO_LONG "Permanent link")

```
HTTP_414_URI_TOO_LONG = 414

```

###  `` HTTP_415_UNSUPPORTED_MEDIA_TYPE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_415_UNSUPPORTED_MEDIA_TYPE "Permanent link")

```
HTTP_415_UNSUPPORTED_MEDIA_TYPE = 415

```

###  `` HTTP_416_RANGE_NOT_SATISFIABLE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_416_RANGE_NOT_SATISFIABLE "Permanent link")

```
HTTP_416_RANGE_NOT_SATISFIABLE = 416

```

###  `` HTTP_417_EXPECTATION_FAILED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_417_EXPECTATION_FAILED "Permanent link")

```
HTTP_417_EXPECTATION_FAILED = 417

```

###  `` HTTP_418_IM_A_TEAPOT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_418_IM_A_TEAPOT "Permanent link")

```
HTTP_418_IM_A_TEAPOT = 418

```

###  `` HTTP_421_MISDIRECTED_REQUEST `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_421_MISDIRECTED_REQUEST "Permanent link")

```
HTTP_421_MISDIRECTED_REQUEST = 421

```

###  `` HTTP_422_UNPROCESSABLE_CONTENT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_422_UNPROCESSABLE_CONTENT "Permanent link")

```
HTTP_422_UNPROCESSABLE_CONTENT = 422

```

###  `` HTTP_423_LOCKED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_423_LOCKED "Permanent link")

```
HTTP_423_LOCKED = 423

```

###  `` HTTP_424_FAILED_DEPENDENCY `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_424_FAILED_DEPENDENCY "Permanent link")

```
HTTP_424_FAILED_DEPENDENCY = 424

```

###  `` HTTP_425_TOO_EARLY `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_425_TOO_EARLY "Permanent link")

```
HTTP_425_TOO_EARLY = 425

```

###  `` HTTP_426_UPGRADE_REQUIRED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_426_UPGRADE_REQUIRED "Permanent link")

```
HTTP_426_UPGRADE_REQUIRED = 426

```

###  `` HTTP_428_PRECONDITION_REQUIRED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_428_PRECONDITION_REQUIRED "Permanent link")

```
HTTP_428_PRECONDITION_REQUIRED = 428

```

###  `` HTTP_429_TOO_MANY_REQUESTS `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_429_TOO_MANY_REQUESTS "Permanent link")

```
HTTP_429_TOO_MANY_REQUESTS = 429

```

###  `` HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE "Permanent link")

```
HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE = 431

```

###  `` HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS "Permanent link")

```
HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS = 451

```

###  `` HTTP_500_INTERNAL_SERVER_ERROR `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR "Permanent link")

```
HTTP_500_INTERNAL_SERVER_ERROR = 500

```

###  `` HTTP_501_NOT_IMPLEMENTED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_501_NOT_IMPLEMENTED "Permanent link")

```
HTTP_501_NOT_IMPLEMENTED = 501

```

###  `` HTTP_502_BAD_GATEWAY `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_502_BAD_GATEWAY "Permanent link")

```
HTTP_502_BAD_GATEWAY = 502

```

###  `` HTTP_503_SERVICE_UNAVAILABLE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_503_SERVICE_UNAVAILABLE "Permanent link")

```
HTTP_503_SERVICE_UNAVAILABLE = 503

```

###  `` HTTP_504_GATEWAY_TIMEOUT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_504_GATEWAY_TIMEOUT "Permanent link")

```
HTTP_504_GATEWAY_TIMEOUT = 504

```

###  `` HTTP_505_HTTP_VERSION_NOT_SUPPORTED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED "Permanent link")

```
HTTP_505_HTTP_VERSION_NOT_SUPPORTED = 505

```

###  `` HTTP_506_VARIANT_ALSO_NEGOTIATES `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_506_VARIANT_ALSO_NEGOTIATES "Permanent link")

```
HTTP_506_VARIANT_ALSO_NEGOTIATES = 506

```

###  `` HTTP_507_INSUFFICIENT_STORAGE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_507_INSUFFICIENT_STORAGE "Permanent link")

```
HTTP_507_INSUFFICIENT_STORAGE = 507

```

###  `` HTTP_508_LOOP_DETECTED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_508_LOOP_DETECTED "Permanent link")

```
HTTP_508_LOOP_DETECTED = 508

```

###  `` HTTP_510_NOT_EXTENDED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_510_NOT_EXTENDED "Permanent link")

```
HTTP_510_NOT_EXTENDED = 510

```

###  `` HTTP_511_NETWORK_AUTHENTICATION_REQUIRED `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED "Permanent link")

```
HTTP_511_NETWORK_AUTHENTICATION_REQUIRED = 511

```

WebSocket codes https://www.iana.org/assignments/websocket/websocket.xml#close-code-number https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent
###  `` WS_1000_NORMAL_CLOSURE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1000_NORMAL_CLOSURE "Permanent link")

```
WS_1000_NORMAL_CLOSURE = 1000

```

###  `` WS_1001_GOING_AWAY `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1001_GOING_AWAY "Permanent link")

```
WS_1001_GOING_AWAY = 1001

```

###  `` WS_1002_PROTOCOL_ERROR `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1002_PROTOCOL_ERROR "Permanent link")

```
WS_1002_PROTOCOL_ERROR = 1002

```

###  `` WS_1003_UNSUPPORTED_DATA `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1003_UNSUPPORTED_DATA "Permanent link")

```
WS_1003_UNSUPPORTED_DATA = 1003

```

###  `` WS_1005_NO_STATUS_RCVD `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1005_NO_STATUS_RCVD "Permanent link")

```
WS_1005_NO_STATUS_RCVD = 1005

```

###  `` WS_1006_ABNORMAL_CLOSURE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1006_ABNORMAL_CLOSURE "Permanent link")

```
WS_1006_ABNORMAL_CLOSURE = 1006

```

###  `` WS_1007_INVALID_FRAME_PAYLOAD_DATA `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1007_INVALID_FRAME_PAYLOAD_DATA "Permanent link")

```
WS_1007_INVALID_FRAME_PAYLOAD_DATA = 1007

```

###  `` WS_1008_POLICY_VIOLATION `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1008_POLICY_VIOLATION "Permanent link")

```
WS_1008_POLICY_VIOLATION = 1008

```

###  `` WS_1009_MESSAGE_TOO_BIG `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1009_MESSAGE_TOO_BIG "Permanent link")

```
WS_1009_MESSAGE_TOO_BIG = 1009

```

###  `` WS_1010_MANDATORY_EXT `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1010_MANDATORY_EXT "Permanent link")

```
WS_1010_MANDATORY_EXT = 1010

```

###  `` WS_1011_INTERNAL_ERROR `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1011_INTERNAL_ERROR "Permanent link")

```
WS_1011_INTERNAL_ERROR = 1011

```

###  `` WS_1012_SERVICE_RESTART `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1012_SERVICE_RESTART "Permanent link")

```
WS_1012_SERVICE_RESTART = 1012

```

###  `` WS_1013_TRY_AGAIN_LATER `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1013_TRY_AGAIN_LATER "Permanent link")

```
WS_1013_TRY_AGAIN_LATER = 1013

```

###  `` WS_1014_BAD_GATEWAY `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1014_BAD_GATEWAY "Permanent link")

```
WS_1014_BAD_GATEWAY = 1014

```

###  `` WS_1015_TLS_HANDSHAKE `module-attribute` [¶](https://fastapi.tiangolo.com/reference/status/#fastapi.status.WS_1015_TLS_HANDSHAKE "Permanent link")

```
WS_1015_TLS_HANDSHAKE = 1015

```

