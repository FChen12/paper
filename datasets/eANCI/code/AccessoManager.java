package Manager;

import java.util.Collection;

import Bean.Accesso;
import DB.DbAccesso;
import DB.DbEccezione;

/**
 * La classe AccessoManager interagisce con le classi di gestione del database
 * La classe AccessoManager non ha dipendenze
 * @author Federico Cinque
 */
public class AccessoManager {
	private DbAccesso dbAccesso;
	/**
	 * Costruttore di default della classe AccessManager
	 */
	public AccessoManager(){
		dbAccesso=new DbAccesso();
	}
	/**
	 * Metodo che permette di controllare la correttezza della login e della 
	 * password di un accesso invocando il relativo metodo della classe db
	 * @param login Stringa che viene usata come login
	 * @param password Stringa che viene usata come password
	 * @return True se l'accesso � presente, False altrimenti
	 * @throws DbEccezione
	 */
	public boolean controllaAccesso(String login, String password)throws DbEccezione{
		return dbAccesso.controllaAccesso(login, password);
	}
	/**
	 * Metodo che permette di controllare l'esistenza della login 
	 * invocando il relativo metodo della classe db
	 * @param login Stringa che viene usata come login
	 * @return True se la login � presente, False altrimenti
	 * @throws DbEccezione
	 */
	public boolean controllaLogin(String login)throws DbEccezione{
		return dbAccesso.controllaLogin(login);
	}
	/**
	 * Metodo che restituisce un accesso invocando il relativo metodo della classe db
	 * @param login Stringa che viene usata come login
	 * @return Restituisce un oggetto di tipo Accesso
	 * @throws DbEccezione
	 */
	public Accesso ottenereAccesso(String login)throws DbEccezione{
		return dbAccesso.ottenereAccesso(login);
	}

	public boolean modificaAccesso(String login, Accesso nuovoAccesso)throws DbEccezione{
		return dbAccesso.modificaAccesso(login, nuovoAccesso);
	}
	/**
	 * Metodo che inserisce un accesso all'interno del db 
	 * invocando il relativo metodo della classe db
	 * @param ac Oggetto di tipo Accesso
	 * @return True se � stato effettuato un inserimento nel db, False altrimenti
	 * @throws DbEccezione
	 */
	public boolean inserisciAccesso(Accesso ac)throws DbEccezione{
		return dbAccesso.inserisciAccesso(ac);
	}
	/**
	 * Metodo che elimina un accesso  dal db invocando il relativo metodo della classe db
	 * @param login Stringa che viene usata come login
	 * @return True se � stato effettuato una cancellazione nel db, False altrimenti
	 * @throws DbEccezione
	 */
	public boolean eliminaAccesso(String login)throws DbEccezione{
		return dbAccesso.eliminaAccesso(login);
	}
	/**
	 * Metodo che restituisce tutti gli accessi memorizzati 
	 * invocando il relativo metodo della classe db
	 * @return Restituisce una Collection di Accessi
	 * @throws DbEccezione
	 */
	public Collection<Accesso> ottenereAccessi()throws DbEccezione{
		return dbAccesso.ottenereAccessi();
	}
}
