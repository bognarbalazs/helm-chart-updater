# Helm Chart Updater

Helm Chart Updater is a tool designed to automate the process of updating Helm charts in your Kubernetes deployments. It simplifies the management of chart versions, ensuring your applications are always running on the latest stable releases.

## Features

- Automated detection of new Helm chart versions
- Customizable update policies
- Integration with CI/CD pipelines
- Supports multiple chart repositories
- Detailed logging and reporting

## Installation

To install the Helm Chart Updater from local source, you can use pip:

```bash
cd helm-chart-updater
pip install .
```

To install Helm Chart Updater from the Gitlab package registry, you can use pip:

```bash
pip install helm-chart-updater --index-url
```

## Usage

To use the Helm Chart Updater, run the following command:

```bash
helm-chart-updater --config <path_of_the_config_file>
```

For more detailed usage instructions and options, run:

```bash
helm-chart-updater --help
```

## Configuration

Create a `version_changes.yaml` file to specify your Helm charts and update policies. Example configuration can be found in the root directory of this repository under name of version_changes.yaml :

Example configuration:

```yaml
base_requirements:
  path_for_charts:
    - /home/user/project/charts/system-a
    - /home/user/project/charts/system-b
  version_requirements:
    - chart_name: microservice
      min_version: 4.2.0
      max_version: 5.1.0
      update_to_version: 5.1.1
version_changes:
  # Microservice chart changes
  4.2.4:
    - action: add_key
      key: ["microservice", "serviceAccount", "create"]
      overwrite: False
      overwrite_value: False
## Example for modifying list elements
### Overwrite existing element
#  4.2.0:
#      - action: add_key
#        key: [ 'microservice', 'env', 1 ]
#        overwrite: True
#        overwrite_value: { 'name': 'SERVER_PORT','value': '8080' }
### Add new element
#      - action: add_key
#        key: [ 'microservice', 'env', 2 ]
#        overwrite: False
#        overwrite_value: { 'name': 'SERVER_USE_SSL','value': 'true' }
```

## Development

To set up the development environment:

1. Clone the repository

2. Create a virtual environment

3. Install the package in editable mode:

```bash
pip install -e .
```

## Testing

To run the test suite:

```bash
pytest
```

### Build and upload package

```bash
python -m build &&
python -m twine upload --repository gitlab-helm-chart-updater dist/*
```

### SSLError

If you get an SSLError, define your ca-certificates.crt file as an environment variable for the requests module

```bash
export REQUESTS_CA_BUNDLE=<path_to_ca-certificates.crt>
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository

2. Create your feature branch ( git checkout -b feature/AmazingFeature)

3. Commit your changes ( git commit -m 'Add some AmazingFeature')

4. Push to the branch ( git push origin feature/AmazingFeature)

5. Open a Merge Request

Please make sure to update tests as appropriate and adhere to the code style guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
