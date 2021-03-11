package Manager;

import java.util.Collection;

import Bean.Cittadino;
import DB.DbCittadino;
import DB.DbEccezione;
/**
 * La classe CittadinoManager interagisce con le classi di gestione del database
 * La classe CittadinoManager non ha dipendenze
 * @author Federico Cinque
 */
public class CittadinoManager {

	private DbCittadino dbCittadino;
	/**
	 * Costruttore di default della classe CIManager
	 */
	public CittadinoManager(){
		dbCittadino = new DbCittadino();
	}
	/**
	 * Metodo che permette la ricerca di un cittadino tramite la sua login
	 * invocando il relativo metodo della classe db
	 * @param login è la login in base alla quale si vuole effettuare la ricerca
	 * @return l'oggetto di tipo cittadino
	 * @throws DbEccezione
	 */
	public Cittadino ottenereCittadinoPerLogin(String login) throws DbEccezione{
		return dbCittadino.ottenereCittadinoPerLogin(login);
	}
	/**
	 * Metodo che permette la modifica della login per uno specifico cittadino
	 * invocando il relativo metodo della classe db
	 * @param idCitt è l'id del cittadino
	 * @param newLogin è la nuova login del cittadino
	 * @return true se l'operazione è andata a buon fine, flase altrimenti
	 */
	public boolean modificaLogin(int idCitt, String newLogin)throws DbEccezione{
		return dbCittadino.modificaLogin(idCitt,newLogin);
	}
	/**
	 * Metodo che permette la modifica dell'indirizzo e-mail di uno specifico cittadino
	 * invocando il relativo metodo della classe db
	 * @param idCittadino è l'identificativo del cittadino
	 * @param email è la nuova mail da assegnare al cittadino
	 * @return true se l'operazione è eseguita con successo, flase altrimenti
	 * @throws DbEccezione
	 */
	public boolean modificaEmail(int idCittadino, String email) throws DbEccezione{
		return dbCittadino.modificaEmailCittadino(idCittadino, email);
	}
	/**
	 * Metodo che permette di inserire un nuovo cittadino
	 * invocando il relativo metodo della classe db
	 * @param cittadino è l'istanza di cittadino
	 * @return l'id del cittadino inserito.
	 * @throws DbEccezione
	 */
	public int inserisciCittadino(Cittadino cittadino)throws DbEccezione{
		return dbCittadino.registraCittadino(cittadino);
	}
	/**
	 * Metodo che permette la ricerca di un insieme di cittadini in base al loro nome e cognome
	 * invocando il relativo metodo della classe db
	 * @param nome parametro su cui effettuare la ricerca
	 * @param cognome parametro su cui effettuare la ricerca
	 * @return una collection di cittadini con il nome e il cognome passato come parametro
	 * @throws DbEccezione
	 */
	public Collection<Cittadino> ricercaCittadino(String nome, String cognome)throws DbEccezione{
		return dbCittadino.ottenereCittadinoPerNome(nome,cognome);
	}
	/**
	 * Metodo che permette la cancellazione di un cittadino
	 * invocando il relativo metodo della classe db
	 * @param idCitt è l'identificativo del cittadino
	 * @return true se l'operazione è eseguita con successo, flase altrimenti
	 * @throws DbEccezione
	 */
	public boolean cancellaCittadino(int idCitt)throws DbEccezione{
		return dbCittadino.cancellaCittadino(idCitt);
	}
	/**
	 * Metodo che permette la ricerca di un cittadino tramite il suo id
	 * invocando il relativo metodo della classe db
	 * @param idCitt è l'identificativo del cittadino
	 * @return oggetto di tipo cittadino con id uguale a quello passato come parametro
	 * @throws DbEccezione
	 */
	public Cittadino ottenereCittadinoPerId(int idCitt)throws DbEccezione{
		return dbCittadino.ottenereCittadinoPerCodice(idCitt);
	}
	/**
	 * Metodo che modifica il nucleo familiare del cittadino dato il suo id
	 * invocando il relativo metodo della classe db
	 * @param idCitt è l'id del cittadino
	 * @param newid è l'id del nuovo nucleo familiare del cittadino
	 * @return true se l'operazione è eseguita con successo, flase altrimenti
	 * @throws DbEccezione
	 */
	public boolean modificaNucleoFamiliare(int idCitt, int nuovoId)throws DbEccezione{
		return dbCittadino.modificaNucleoFamiliareCittadino(idCitt, nuovoId);
	}
	/**
	 * Metodo che permette la modifica del nome di uno specifico cittadino
	 * invocando il relativo metodo della classe db
	 * @param idCitt è l'identificativo del cittadino
	 * @param nome è il nuovo nome da assegnare al cittadino
	 * @return true se l'operazione è eseguita con successo, flase altrimenti
	 * @throws DbEccezione
	 */
	public boolean modificaNome(int idCitt, String nome)throws DbEccezione{
		return dbCittadino.modificaNomeCittadino(idCitt, nome);
	}
	/**
	 * Metodo che permette la modifica del cognome di uno specifico cittadino
	 * invocando il relativo metodo della classe db
	 * @param idCitt è l'identificativo del cittadino
	 * @param cognome è il nuovo cognome da assegnare al cittadino
	 * @return true se l'operazione è eseguita con successo, flase altrimenti
	 * @throws DbEccezione
	 */
	public boolean modificaCognome(int idCitt, String cognome)throws DbEccezione{
		return dbCittadino.modificaCognomeCittadino(idCitt, cognome);
	}
}
