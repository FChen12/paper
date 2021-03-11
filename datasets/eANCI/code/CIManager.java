package Manager;

import Bean.CartaIdentita;
import DB.*;
/**
 * La classe CIManager interagisce con le classi di gestione del database
 * La classe CIManager non ha dipendenze
 * @author Federico Cinque
 */
public class CIManager {
	private DbCartaIdentita dbCartaIdentita;
	/**
	 * Costruttore di default della classe CIManager
	 */
	public CIManager(){
		dbCartaIdentita = new DbCartaIdentita();
	}
	/**
	 * Metodo che permette la ricerca di una carta d'identita tramite il suo numero
	 * invocando il relativo metodo della classe db
	 * @param cod il numero della carta d'identità del cittadino.
	 * @return l'oggetto di tipo CartaIdentità associata al numero passato come parametro
	 * @throws DbEccezione
	 */
	public CartaIdentita ottenereCartaPerNumero(String cod)throws DbEccezione{
		return dbCartaIdentita.ricercaCartaIdentitaPerNumero(cod);
	}
	
	public CartaIdentita ottenereCartaPerIdCStri(int id)throws DbEccezione{
		return dbCartaIdentita.ricercaCartaIdentitaPerProprietario(id);
	}
	
}
