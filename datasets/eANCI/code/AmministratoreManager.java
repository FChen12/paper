package Manager;

import java.util.Collection;

import Bean.Amministratore;
import DB.DbAmministratore;
import DB.DbEccezione;
/**
 * La classe AdminManager interagisce con le classi di gestione del database
 * La classe AdminManager non ha dipendenze
 * @author Federico Cinque
 */
public class AmministratoreManager {
	private DbAmministratore dbAmministratore;
	/**
	 * Costruttore di default della classe AdminManager
	 */
	public AmministratoreManager(){
		dbAmministratore = new DbAmministratore();
	}
	/**
	 * Metodo che modifica un amministratore
	 * invocando il relativo metodo della classe db
	 * @param matricola la stringa che identifica l'amministratore
	 * @param newAdmin Amministratore con i dati aggiornati
	 * @return True se è stato effettuato un inserimento nel db, False altrimenti
	 */
	public boolean modificaAdmin(String matricola, Amministratore nuovoAdmin)throws DbEccezione{
		return dbAmministratore.modificaAmministratore(matricola, nuovoAdmin);
	}
	/**
	 * Metodo che restituisce un amministratore
	 * invocando il relativo metodo della classe db
	 * @param matricola stringa che viene utilizzato come matricola dell'amministratore
	 * @return Restituisce un oggetto di tipo Amministratore
	 * @throws DbEccezione
	 */
	public Amministratore ricercaAdminByMatricola(String matricola)throws DbEccezione{
		return dbAmministratore.ottenereAmministratorePerMatricola(matricola);
	}
	/**
	 * Metodo che inserisce un amministratore all'interno del db
	 * invocando il relativo metodo della classe db
	 * @param newAdmin Oggetto di tipo Amministratore
	 * @return True se è stato effettuato un inserimento nel db, False altrimenti
	 * @throws DbEccezione
	 */
	public boolean inserisciAdmin(Amministratore nuovoAdmin)throws DbEccezione{
		return dbAmministratore.inserisciAmministratore(nuovoAdmin);
	}
	/**
	 * Metodo che elimina un Amministratore  dal db
	 * invocando il relativo metodo della classe db
	 * @param matricola l'intero che viene utilizzato come matricola
	 * @return True se è stato effettuato una cancellazione nel db, False altrimenti
	 * @throws DbEccezione
	 */
	public String eliminaAmministratore(String matricola)throws DbEccezione{
		Collection<Amministratore> Amministratori = dbAmministratore.ottenereAmministratori();
		if(Amministratori.size()>1){
			if(dbAmministratore.eliminaAmministratore(matricola))
				return "ok";
			else
				return "errore";
		}
		else
			return "unico";
	}
	/**
	 * Metodo che restituisce un amministratore
	 * invocando il relativo metodo della classe db
	 * @param login stringa che viene utilizzata come login dell'amministratore
	 * @return Restituisce un oggetto di tipo amministratore
	 * @throws DbEccezione
	 */
	public Amministratore ottenereAmministratorePerLogin(String login) throws DbEccezione{
		return dbAmministratore.ottenereAmministratorePerLogin(login);
	}
	/** Metodo che restituisce un insieme di amministratori
	 * invocando il relativo metodo della classe db
	 * @param nomeAmm stringa che viene utilizzata come nome dell'amministratore
	 * @param cognAmm stringa che viene utilizzata come cognome dell'amministratore
	 * @return Restituisce una Collection di Amministratori
	 * @throws DbEccezione
	 */
	public Collection<Amministratore> ottenereAmministratorePerNome(String nomeAmm,String cognAmm) throws DbEccezione{
		return dbAmministratore.ottenereAmministratorePerNome(nomeAmm, cognAmm);
	}
	/**
	 * Metodo che restituisce tutti gli amministratori memorizzati
	 * @return Restituisce una Collection di Amministratori
	 * @throws DbEccezione
	 */
	public Collection<Amministratore> ottenereAmministratori() throws DbEccezione{
		return dbAmministratore.ottenereAmministratori();
	}
}
