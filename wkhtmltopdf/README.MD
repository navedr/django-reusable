### Usage
```bash
docker pull navedrangwala/wkhtmltopdf
```
```bash
docker run --rm -v /Users/narangwa/www:/Users/narangwa/www navedrangwala/wkhtmltopdf https://www.google.com /Users/narangwa/www/google.pdf
```

### Build
```bash
docker build --platform linux/amd64 . -t navedrangwala/wkhtmltopdf:latest
```