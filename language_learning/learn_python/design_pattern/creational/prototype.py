from typing import Self, Any
from pydantic import BaseModel, Field

# 1. The Prototype Model
# Pydantic models are perfect for this as they handle nested validation.
class NetworkConfig(BaseModel):
    vlan: int
    ip_range: str
    firewall_enabled: bool = True

class VirtualMachine(BaseModel):
    name: str
    os: str
    cpu_cores: int = Field(gt=0)
    ram_gb: int = Field(gt=0)
    network: NetworkConfig

    def clone(self, **overrides: Any) -> Self:
        """
        The core of the Prototype pattern.
        Creates a deep copy and applies any specific changes (overrides).
        """
        # Pydantic V2 model_copy(deep=True) ensures nested objects 
        # (like NetworkConfig) are also copied, not just referenced.
        return self.model_copy(update=overrides, deep=True)

# 2. The Prototype Registry
# This class stores "Master" versions of objects to be cloned later.
class VMRegistry:
    def __init__(self):
        self._prototypes: dict[str, VirtualMachine] = {}

    def register_prototype(self, name: str, vm: VirtualMachine) -> None:
        self._prototypes[name] = vm

    def get_prototype(self, name: str) -> VirtualMachine:
        proto = self._prototypes.get(name)
        if not proto:
            raise ValueError(f"Prototype '{name}' not found.")
        return proto.clone() # Return a clone, not the master original

# 3. Execution
def main():
    registry = VMRegistry()

    # --- Setup Master Prototypes ---
    linux_proto = VirtualMachine(
        name="Base-Linux-Server",
        os="Ubuntu 24.04",
        cpu_cores=2,
        ram_gb=4,
        network=NetworkConfig(vlan=10, ip_range="10.0.0.x")
    )
    registry.register_prototype("standard_linux", linux_proto)

    # --- Use the Prototype Pattern ---
    
    # Client 1: Wants a standard Linux server but with 16GB RAM
    web_server = registry.get_prototype("standard_linux").clone(
        name="Web-Server-01", 
        ram_gb=16
    )

    # Client 2: Wants a standard Linux server but on a different VLAN
    db_server = registry.get_prototype("standard_linux").clone(
        name="DB-Server-01"
    )
    # We can also modify the nested attributes because it's a deep copy
    db_server.network.vlan = 20

    # --- Verification ---
    print(f"Prototype RAM: {linux_proto.ram_gb}GB")
    print(f"Web Server RAM: {web_server.ram_gb}GB")
    
    print("-" * 20)
    
    print(f"Prototype VLAN: {linux_proto.network.vlan}")
    print(f"DB Server VLAN: {db_server.network.vlan}")

    # Check if they are different objects in memory
    print(f"Is DB Server a new object? {db_server is linux_proto}")

if __name__ == "__main__":
    main()