#Esecizio sui metodi di pagamento e il polimorfismo


class MeodoPagamento():
    
    def effettua_pagamento(self, importo: float):
        return f"Pagamento di {importo}€ effettuato con succeso!"
    
# Classi figlie di MetodoPagamento

class CartaDiCredito(MeodoPagamento):
    def __init__(self):
        super().__init__()
        
    def effettua_pagamento(self, importo: float):
        numeri_carta = input('Dammi i numeri della carta di credito: ')
        scadenza = input('Dammi la scadenza: ')
        codice_segreto = input('Dammi il codice segreto: ')
        return super().effettua_pagamento(importo) + f" - Carta di credito con numeri: {numeri_carta}, scadenza: {scadenza}, codice segreto: {codice_segreto}"
    

class PayPal(MeodoPagamento):
    def __init__(self):
        super().__init__()
        
    def effettua_pagamento(self, importo: float):
        emai = input('Inserisci email: ')
        password = input('Inserisci la password: ')
        return super().effettua_pagamento(importo) + f" - Attraverso PayPal, account: {emai}, password: {''.join('*' for c in password)})"
    

class BonificoBancario(MeodoPagamento):
    def __init__(self):
        super().__init__()
        
    def effettua_pagamento(self, importo: float):
        intestatario = input('Inserisci Intestatario: ')
        iban = input('Inserisci IBAN: ')
        return super().effettua_pagamento(importo) + f" - Attraverso Bonifico, IBAN: {iban}, Intestatario: {intestatario})"


# Gestore dei pagamenti che utilizza le istanze
class GestionePagamento():
    __saldo = 0
    
    def __init__(self):
        pass
    
    # Metodo privado che gestisce il pagamento
    def __effettua_pagamento(self, tipo_pagamento, importo):
        # print((isinstance(tipo_pagamento, CartaDiCredito) or isinstance(tipo_pagamento, PayPal) or isinstance(tipo_pagamento, BonificoBancario)))
        if isinstance(importo, float) and importo>0 :
            msg = tipo_pagamento.effettua_pagamento(importo)
            return msg
        else: "Errore durante il pagamento, importo non valido!"
    
    # Metodo che permette di pagare
    def paga(self):
        #Menu
        while True:
            print("\nMetodi di pagamento:")
            print("1. Carta di Credito")
            print("2. PayPal")
            print("3. Bonifico Bancario")
            print("4. Esci")
            
            scelta = input("Scegli un metodo di pagamento: ")
            
            if scelta == '4':
                print("\nArrivedeci :).")
                break
            
            elif scelta in ['1', '2', '3']:
                while True:
                    temp_importo = input("Inserisci l'importo da pagare: ")
                    if temp_importo.isdigit(): # Controlla che ho inserito un numero
                        importo = float(temp_importo)
                        
                        if scelta == '1':
                            print(self.__effettua_pagamento(CartaDiCredito(), importo)) # Utilizza il metodo privato per effettuare il pagamento
                        elif scelta == '2':
                            print(self.__effettua_pagamento(PayPal(), importo))
                        elif scelta == '3':
                            print(self.__effettua_pagamento(BonificoBancario(), importo))
                        
                        break #Esci
                    else:
                        print("Attenzione! Inserire un numero.\n")
                        
    def set_saldo(self):
        while True:
            temp_saldo = input("Deposita nel saldo saldo: ")
            if temp_saldo.isdigit(): # Controlla che ho inserito un numero
                self.__saldo += float(temp_saldo)
                self.get_saldo()
                break
            else:
                print("Attenzione! Inserire un numero.\n")
    
    def get_saldo(self):
        print(f"Saldo: {self.__saldo}")
                        
            
pagamento = GestionePagamento()

pagamento.set_saldo()
pagamento.paga()


