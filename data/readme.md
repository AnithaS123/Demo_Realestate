# Synthetic data

All files in this directory are fictional demonstration fixtures. They are not valid identity, bank, employment, sanctions, or property records.

For application setup, model access, IAM trust/policy templates, and the demo Lambda, see the project-level [README](../README.md) and [IAM guide](../iam/README.md). Do not store credentials, account-specific ARNs, or policy-generation scripts in this data directory.


git clone <repo>
cd <repo>
cp ~/Desktop/.env .
make check && make setup && make deploy && make verify && make run