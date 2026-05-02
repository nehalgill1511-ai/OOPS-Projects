from __future__ import annotations
from datetime import date
from typing import Dict, List, Tuple

Txn = Tuple[str, str, float, float]  # (iso_date, type, amount, balance_after)


class Account:
    def __init__(self, account_id: str, owner: str):
        self.account_id = account_id
        self.owner = owner
        self.__balance: float = 0.0
        self._history: List[Txn] = []

    def _record(self, typ: str, amount: float) -> None:
        txn = (date.today().isoformat(), typ, amount, self.__balance)
        self._history.append(txn)

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        self.__balance += amount
        self._record("DEPOSIT", amount)

    def get_balance(self) -> float:
        return self.__balance

    def _set_balance(self, new_balance: float) -> None:
        self.__balance = new_balance

    def withdraw(self, amount: float) -> None:
        raise NotImplementedError("Use subclass implementation")

    def transfer(self, to: "Account", amount: float) -> None:
        if self.account_id == to.account_id:
            raise ValueError("Cannot transfer to the same account")
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        # Save original balances for rollback
        original_self_balance = self.get_balance()
        original_to_balance = to.get_balance()

        try:
            self.withdraw(amount)
            to.deposit(amount)

            # Record transfer events separately
            self._record("TRANSFER_OUT", amount)
            to._record("TRANSFER_IN", amount)

        except Exception:
            # Rollback
            self._set_balance(original_self_balance)
            to._set_balance(original_to_balance)
            raise

    def statement(self) -> List[Txn]:
        return list(self._history)


class SavingsAccount(Account):
    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if amount > self.get_balance():
            raise ValueError("Insufficient funds")

        self._set_balance(self.get_balance() - amount)
        self._record("WITHDRAW", amount)


class CurrentAccount(Account):
    def __init__(self, account_id: str, owner: str, overdraft_limit: float = 5000.0):
        super().__init__(account_id, owner)
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        new_balance = self.get_balance() - amount

        if new_balance < -self.overdraft_limit:
            raise ValueError("Overdraft limit exceeded")

        self._set_balance(new_balance)
        self._record("WITHDRAW", amount)


class Bank:
    def __init__(self):
        self.accounts: Dict[str, Account] = {}

    def open_account(self, account: Account) -> None:
        if account.account_id in self.accounts:
            raise ValueError(f"Account ID '{account.account_id}' already exists")

        self.accounts[account.account_id] = account

    def get_account(self, account_id: str) -> Account:
        try:
            return self.accounts[account_id]
        except KeyError:
            raise KeyError(f"Account '{account_id}' not found")

    def transfer(self, from_id: str, to_id: str, amount: float) -> None:
        from_acc = self.get_account(from_id)
        to_acc = self.get_account(to_id)

        from_acc.transfer(to_acc, amount)


# ===== Example Usage =====
if __name__ == "__main__":
    bank = Bank()

    acc1 = SavingsAccount("A001", "Ali")
    acc2 = CurrentAccount("A002", "Ahmed", overdraft_limit=2000)

    bank.open_account(acc1)
    bank.open_account(acc2)

    acc1.deposit(1000)
    acc2.deposit(500)

    bank.transfer("A001", "A002", 300)

    acc2.withdraw(1000)  # uses overdraft

    print("Ali Balance:", acc1.get_balance())
    print("Ahmed Balance:", acc2.get_balance())

    print("\nAli Statement:")
    for txn in acc1.statement():
        print(txn)

    print("\nAhmed Statement:")
    for txn in acc2.statement():
        print(txn)
