# HealthSyncAIBackend

## Configuration Setup

This project uses a configuration module built with [Pydantic's BaseSettings](https://pydantic.dev/latest/concepts/pydantic_settings/) to manage environment variables and secure settings for the application. These settings are automatically loaded and validated from your environment or a `.env` file.

### Supported Environment Variables

- **DATABASE_URI**: The URI for connecting to your database.  
  _Example_: `postgresql://user:password@localhost/dbname`

- **SECRET_KEY**: A secret key used for cryptographic operations such as JWT token signing.  
  _Example_: `your_very_secret_key`

- **API_ENDPOINT**: The URL of the external API your application will integrate with.  
  _Example_: `https://api.example.com`

- **DEBUG**: A boolean flag to enable or disable debug mode.  
  _Example_: `True`

### .env File Example

Create a `.env` file in the project's root directory with values similar to the following:
```
DATABASE_URI=postgresql://user:password@localhost/dbname
SECRET_KEY=your_very_secret_key
API_ENDPOINT=https://api.example.com
DEBUG=True
```
The engine is created in `app/db/init_db.py` as shown below:
