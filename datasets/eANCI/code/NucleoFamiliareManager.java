package Manager;

import Bean.NucleoFamiliare;
import DB.DbEccezione;
import DB.DbNucleoFamiliare;
/**
 * La classe NucleoFamiliareManager interagisce con le classi di gestione del database
 * La classe NucleoFamiliareManager non ha dipendenze
 * @author Federico Cinque
 */
public class NucleoFamiliareManager {

	private DbNucleoFamiliare nucleoF;
	/**
	 * Costruttore di default della classe NucleoFamiliareManager
	 */
	public NucleoFamiliareManager(){
		nucleoF = new DbNucleoFamiliare();
	}
	/**
	 * Metodo che inserisci un oggetto nucleoFamiliare nel db
	 * invocando il relativo metodo della classe db
	 * @param nf Oggetto di tipo nucleofamiliare
	 * @return Restituisce l'id del nucleo familiare inserito
	 * @throws DbEccezione
	 */
	public int inserisciNucleo(NucleoFamiliare nf){
		return nucleoF.inserisciNucleoFamiliare(nf);
	}
	/**
	 * Metodo che permette di controllare l’esistenza di un nucleo familiare
	 * invocando il relativo metodo della classe db
	 * @param id l'intero che viene utilizzato come id del nucleo familiare
	 * @return True se l'id Ë presente, False altrimenti
	 * @throws DbEccezione 
	 */
	public boolean controllaidFamiglia(int id){
		return nucleoF.controllaIdFamiglia(id);
	}
	/**
	 * Metodo che restituisce il numero di componenti del nucleo familiare
	 * invocando il relativo metodo della classe db
	 * @param id del nucleo familiare di cui si vuole il numero di componenti
	 * @return True se l'id Ë presente, False altrimenti
	 * @throws DbEccezione 
	 */
	public int ottenereNComponentiNucleo(int id){
		return nucleoF.ottenereNucleoFamiliarePerId(id).ottenereNComponenti();
	}
	/**
	 * Metodo che modifica un capo famiglia
	 * invocando il relativo metodo della classe db
	 * @param id l'intero che viene utilizzato come id della famiglia
	 * @param IdCitt l'intero che viene utilizzato come id del capo famiglia
	 * @return True se la modifica ha avuto successo, altrimenti False
	 * @throws DbEccezione
	 */
	public boolean settareCapoFamiglia(int id, int IdCitt){
		return nucleoF.settareCapoFamiglia(id, IdCitt);
	}
	/**
	 * Metodo che incrementa il numero di componenti del nucleo familiare
	 * invocando un metodo della classe db
	 * @param id del nucleo familiare che si vuole modificare
	 * @return True se la modifica ha avuto successo, altrimenti False
	 * @throws DbEccezione 
	 */
	public boolean incrementaComponenti(int id){
		int n = ottenereNComponentiNucleo(id)+1;
		return nucleoF.settareNComponenti(id,n);
	}
	/**
	 * Metodo che decrementa il numero di componenti del nucleo familiare
	 * invocando un metodo della classe db
	 * @param id del nucleo familiare che si vuole modificare
	 * @return True se la modifica ha avuto successo, altrimenti False
	 * @throws DbEccezione 
	 */
	public boolean decrementaComponenti(int id){
		int n = ottenereNComponentiNucleo(id)-1;
		return nucleoF.settareNComponenti(id,n);
	}
	
	public NucleoFamiliare ottenereNucleo(int id) {
		return nucleoF.ottenereNucleoFamiliarePerId(id);
	}
}
