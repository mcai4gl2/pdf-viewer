# REST API Documentation

## Upload Document API

### Endpoint

`POST /upload`

### Description

This endpoint allows users to upload a new PDF document along with its metadata, change description, and optional HTML files.

### Request

#### Method

`POST`

#### Content-Type

`multipart/form-data`

#### Parameters

| Name              | Type     | Description                                                              | Required |
| :---------------- | :------- | :----------------------------------------------------------------------- | :------- |
| `doc_id`          | `string` | A unique identifier for the document.                                    | Yes      |
| `metadata`        | `string` | A JSON string containing additional metadata for the document.           | No       |
| `change_description` | `string` | A description of the changes made to the document.                       | No       |
| `file`            | `file`   | The PDF file to be uploaded.                                             | Yes      |
| `html_files`      | `file[]` | An array of HTML files associated with the document (optional).          | No       |

### Responses

#### `200 OK`

Document uploaded successfully.

```json
{
    "message": "Document uploaded successfully",
    "doc_id": "your_doc_id"
}
```

#### `400 Bad Request`

Invalid request, missing parameters, or invalid file type.

```json
{
    "error": "Error message describing the issue"
}
```

#### `500 Internal Server Error`

An unexpected error occurred on the server.

```json
{
    "error": "Internal server error"
}
```

## Delete Document Version API

### Endpoint

`DELETE /documents/<doc_id>/versions/<version_number>`

### Description

This endpoint allows for the deletion of a specific version of a document. If the deleted version is the last remaining version of a document, the document itself will also be removed.

### Request

#### Method

`DELETE`

#### URL Parameters

| Name           | Type     | Description                                  | Required |
| :------------- | :------- | :------------------------------------------- | :------- |
| `doc_id`       | `string` | The unique identifier of the document.       | Yes      |
| `version_number` | `integer` | The version number to be deleted.            | Yes      |

### Responses

#### `200 OK`

Version deleted successfully.

```json
{
    "success": true,
    "message": "Version deleted successfully."
}
```

#### `400 Bad Request`

Invalid request, document or version not found.

```json
{
    "success": false,
    "error": "Error message describing the issue"
}
```

## Submit Vote API

### Endpoint

`POST /vote`

### Description

This endpoint allows users to submit a vote (good or bad) for a specific document version.

### Request

#### Method

`POST`

#### Content-Type

`application/json`

#### Body Parameters

| Name        | Type     | Description                                  | Required |
| :---------- | :------- | :------------------------------------------- | :------- |
| `doc_id`    | `string` | The unique identifier of the document.       | Yes      |
| `version`   | `integer` | The version number being voted on.           | Yes      |
| `vote_type` | `string` | The type of vote: 'good' or 'bad'.         | Yes      |

### Responses

#### `200 OK`

Vote recorded successfully.

```json
{
    "success": true,
    "message": "Vote recorded successfully."
}
```

#### `400 Bad Request`

Invalid request, missing parameters, invalid vote type, or document/version not found.

```json
{
    "success": false,
    "error": "Error message describing the issue"
}
```

## Get Vote Results API

### Endpoint

`GET /vote_results`

### Description

This endpoint retrieves all individual vote records, including the document ID, version, vote type, voter information (IP address), and timestamp.

### Request

#### Method

`GET`

#### URL Parameters

None.

### Responses

#### `200 OK`

An array of vote objects.

```json
[
    {
        "doc_id": "document_id_1",
        "version": 1,
        "vote_type": "good",
        "voter_info": "192.168.1.1",
        "created_at": "YYYY-MM-DD HH:MM:SS"
    },
    {
        "doc_id": "document_id_1",
        "version": 1,
        "vote_type": "bad",
        "voter_info": "192.168.1.2",
        "created_at": "YYYY-MM-DD HH:MM:SS"
    }
]
```

#### `500 Internal Server Error`

An unexpected error occurred on the server.

```json
{
    "error": "Internal server error"
}
```