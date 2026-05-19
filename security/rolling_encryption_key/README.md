# Envelope encryption (DEK + KEK)

A minimal Python demo of **envelope encryption**: encrypt data with a **Data Encryption Key (DEK)**, then encrypt that DEK with a **Key Encryption Key (KEK)** held in a simulated KMS.

## Run

```bash
pip install cryptography
python dek_kek_rolling.py
```

The script prints each step: KEK setup, envelope creation, data encryption, DEK wipe, and round-trip decryption.

---

## What is envelope encryption?

Envelope encryption is a security practice where you encrypt your data with one key, and then encrypt that key with another key.

It is called "envelope" encryption because it mimics placing a letter inside a physical envelope. Anyone can see the envelope, but only someone with the key to open the envelope can read the letter inside.

## The two keys involved

| Key | Role |
|-----|------|
| **Data Encryption Key (DEK)** | A fast, symmetric key used to encrypt the actual data (files, database rows, etc.). |
| **Key Encryption Key (KEK)** | A master key used solely to encrypt and protect the DEK. The KEK never leaves a highly secure Key Management Service (KMS). |

---

## Step-by-step: how it works

### Phase 1: Encrypting the data (locking the envelope)

1. **Request a key:** Your application asks the KMS for a new data key.
2. **KMS generates two versions:** The KMS creates a DEK and returns:
   - The **plaintext DEK** (unlocked).
   - The **ciphertext DEK** (encrypted by the KMS using the master KEK).
3. **Encrypt the data:** Your application uses the plaintext DEK to encrypt your data.
4. **Save everything together:** Your application stores the encrypted data and the ciphertext DEK together in the database.
5. **Wipe memory:** The application securely deletes the plaintext DEK from its memory.

### Phase 2: Decrypting the data (opening the envelope)

1. **Retrieve the package:** Your application reads the encrypted data and the ciphertext DEK from the database.
2. **Send the key back:** Your application sends only the ciphertext DEK to the KMS.
3. **KMS decrypts the key:** The KMS uses the master KEK to decrypt it and returns the plaintext DEK.
4. **Decrypt the data:** Your application uses the plaintext DEK to unlock the data.

---

## Why use envelope encryption?

- **Network performance:** Encrypting massive files directly via a cloud KMS is slow and uses too much bandwidth. With envelope encryption, only the tiny DEK travels over the network.
- **Centralized control:** You can instantly cut off access to your data by revoking access to the master KEK in the KMS.
- **Easy key rotation:** You can update the master KEK to protect the DEKs without needing to re-encrypt terabytes of raw data.

---

## Code map

| File / class | Purpose |
|--------------|---------|
| `dek_kek_rolling.py` | End-to-end demo using `cryptography.fernet` |
| `KMS` | Owns the master KEK; `generate_data_key()` returns plaintext + ciphertext DEK; `decrypt_data_key()` unwraps envelopes |
| `Database` | Persists encrypted data and the ciphertext DEK side by side |
| `Application` | `write()` encrypts via envelope encryption; `read()` loads from the DB and unwraps the DEK via KMS |

In production, the KEK stays inside **AWS KMS**, **Google Cloud KMS**, **Azure Key Vault**, or similar — your app never holds the master key in memory.
