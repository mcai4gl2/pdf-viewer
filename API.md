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