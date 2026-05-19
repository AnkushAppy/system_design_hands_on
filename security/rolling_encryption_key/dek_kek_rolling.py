from dataclasses import dataclass

from cryptography.fernet import Fernet


@dataclass(frozen=True)
class DataKey:
    """Two versions of the same DEK returned by KMS."""

    plaintext: bytes   # unlocked — used locally to encrypt data, then wiped
    ciphertext: bytes  # wrapped by the master KEK — safe to store alongside data


class KMS:
    """Simulated Key Management Service. The master KEK never leaves here."""

    def __init__(self, master_kek: bytes | None = None) -> None:
        self._master_kek = master_kek or Fernet.generate_key()
        self._protector = Fernet(self._master_kek)

    @property
    def master_kek(self) -> bytes:
        return self._master_kek

    def generate_data_key(self) -> DataKey:
        """Create a DEK and return both the plaintext and ciphertext versions."""
        plaintext_dek = Fernet.generate_key()
        ciphertext_dek = self._protector.encrypt(plaintext_dek)
        return DataKey(plaintext=plaintext_dek, ciphertext=ciphertext_dek)

    def decrypt_data_key(self, ciphertext_dek: bytes) -> bytes:
        """Unwrap a ciphertext DEK using the master KEK."""
        return self._protector.decrypt(ciphertext_dek)


class Database:
    """Stores encrypted payloads and their key envelopes side by side."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, bytes]] = {}

    def write(self, record_id: str, encrypted_data: bytes, key_envelope: bytes) -> None:
        self._records[record_id] = {
            "data": encrypted_data,
            "key_envelope": key_envelope,
        }

    def read(self, record_id: str) -> tuple[bytes, bytes]:
        record = self._records[record_id]
        return record["data"], record["key_envelope"]


class Application:
    """Encrypts data on write and decrypts on read using envelope encryption."""

    def __init__(self, kms: KMS, database: Database) -> None:
        self._kms = kms
        self._database = database

    def write(self, record_id: str, plaintext: bytes) -> None:
        # 1. Ask KMS for a new data key (plaintext + ciphertext versions)
        data_key = self._kms.generate_data_key()
        print(f"[KMS] Plaintext DEK:  {data_key.plaintext.decode()}")
        print(f"[KMS] Ciphertext DEK: {data_key.ciphertext.decode()}")

        # 2. Encrypt the data locally with the plaintext DEK
        print(f"[App] Plaintext: {plaintext.decode()}")
        encrypted_data = Fernet(data_key.plaintext).encrypt(plaintext)
        print(f"[App] Encrypted Data: {encrypted_data.decode()}")

        # 3. Wipe the plaintext DEK from application memory
        plaintext_dek = data_key.plaintext
        del plaintext_dek
        print("[App] Erased Plaintext DEK from application memory.\n")

        # 4. Persist encrypted data + wrapped DEK together
        self._database.write(record_id, encrypted_data, data_key.ciphertext)

    def read(self, record_id: str) -> bytes:
        # 1. Load the encrypted package from storage
        encrypted_data, key_envelope = self._database.read(record_id)
        print(f"[App] Encrypted Data: {encrypted_data} bytes")
        print(f"[App] Key Envelope: {key_envelope} bytes")

        # 2. Send only the envelope to KMS; get back the plaintext DEK
        plaintext_dek = self._kms.decrypt_data_key(key_envelope)
        print(f"[KMS] Decrypted envelope to Plaintext DEK: {plaintext_dek.decode()}")

        # 3. Decrypt the data locally
        return Fernet(plaintext_dek).decrypt(encrypted_data)


def main() -> None:
    kms = KMS()
    database = Database()
    app = Application(kms, database)

    print("--- 0. KMS Setup ---")
    print(f"Master Key (KEK): {kms.master_kek.decode()}\n")

    print("--- Phase 1: Encryption ---")
    secret_message = b"Top secret database record data."
    app.write("record-1", secret_message)

    print("--- Phase 2: Decryption ---")
    original_message = app.read("record-1")
    print(f"[App] Decrypted Message: {original_message.decode()}")


if __name__ == "__main__":
    main()
