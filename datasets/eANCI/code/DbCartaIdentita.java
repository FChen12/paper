package DB;
import Bean.*;
import java.sql.*;

import Bean.CartaIdentita;


/**
 * Classe che si occupa di gestire le connessioni con 
 * il database e di schermare le servlet dal DBMS.
 * @author Michelangelo Cianciulli
 *
 */
public class DbCartaIdentita 
{
	private Connection connection;
	
	public DbCartaIdentita() throws DbEccezione
	{	
		try
		{
			connection=DbConnessione.ottenereConnection();
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore : connessione non riuscita");
		}
	}
	/**
	 * Metodo che permette la ricerca di una carta d'identit‡ tramite il suo numero.
	 * @param cod Ë il numero della carta d'identit‡† del cittadino.
	 * @return l'oggetto di tipo CartaIdentit‡† associata al numero passato come parametro
	 * @throws DbEccezione
	 */
	public CartaIdentita ricercaCartaIdentitaPerNumero (String cod) throws DbEccezione
	{	
		CartaIdentita res = null;
		ResultSet rs = null;
		PreparedStatement stmt = null;
		boolean e;
		try
		{
			stmt = connection.prepareStatement("SELECT * FROM cartaidentita WHERE numero = ?");
			stmt.setString(1, cod);
			rs = stmt.executeQuery();
		if(rs.next()==true)
			{
				String num = rs.getString("numero");
				int citt = rs.getInt("cittadino");
				String cittadinanza = rs.getString("cittadinanza");
				String residenza =rs.getString("residenza");
				String via = rs.getString("via");
				int numciv = rs.getInt("numeroCivico");
				String statoCivile = rs.getString("statoCivile");
				String professione = rs.getString("professione");
				double statura = rs.getDouble("statura");
				String capelli = rs.getString("capelli");
				String occhi = rs.getString("occhi");
				String segniParticolari = rs.getString("segniParticolari");
				java.util.Date dataRilascio = rs.getDate("dataRilascio");
				java.util.Date dataScadenza = rs.getDate("dataScadenza");
				int esp = rs.getInt("validaEspatrio");
				if(esp == 1)
					e=true;
				else 
					e=false;
				res = new CartaIdentita(num,citt,cittadinanza,residenza,via,numciv,statoCivile,professione,statura,capelli,occhi,segniParticolari,dataRilascio,dataScadenza,e);
				}
			return res;
		}
		catch (SQLException exc)
		{
			throw new DbEccezione("Errore ricerca carta d'identit√† tramite il suo numero");
		}
		finally
		{
			try 
			{
				if(rs!=null)
					rs.close();
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e1) 
			{
				throw new DbEccezione("Errore ricerca carta d'identit√† tramite il suo numero");
			}
		}
	}
	
	/**
	 * Metodo che permette la cancellazione di una carta d'identit‡†. (aggiornamento del db)
	 * @param cod Ë® il codice della carta d'identit‡† che si intende cancellare
	 * @return true se l'operazione Ë andata a buon fine
	 * @throws DbEccezione
	 */
	public boolean cancellaCartaIdentita (String cod) throws DbEccezione
	{	
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("DELETE FROM cartaidentita WHERE numero = ?");
			stmt.setString(1, cod);
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore cancellazione carta identit√†");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore cancellazione carta identit√†");
			}
		}
	}

	
	/**
	 * Metodo che permette la registrazione di una nuova carta d'identit‡ all'interno del database
	 * @param c Ë l'oggetto di tipo carta d'identit‡
	 * @return true se l'operazione Ë andata a buon fine
	 * @throws DbEccezione
	 */
	public boolean registraCartaIdentita (CartaIdentita c) throws DbEccezione
	{	
		int esp;
		String num = c.ottenereNumero();
		int citt = c.id();
		String cittadinanza = c.ottenereCittadinanza();
		String residenza = c.ottenereResidenza();
		String via = c.ottenereVia();
		int numCiv = c.ottenereNumCivico();
		String statoCiv = c.ottenereStatoCivile();
		String professione = c.ottenereProfessione();
		double statura = c.ottenereStatura();
		String capelli = c.ottenereCapelli();
		String occhi = c.ottenereOcchi();
		String segniParticolari = c.ottenereSegniParticolari();
		java.util.Date dataRilascio = c.ottenereDataRilascio();
		java.util.Date dataScadenza = c.ottenereDataScadenza();
		if(c.isValidaEspatrio())
			esp = 1;
		else 
			esp = 0;
		
		PreparedStatement stmt = null;
		
		try
		{
			stmt = connection.prepareStatement("INSERT INTO cartaidentita VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)");
			stmt.setString(1,num);
			stmt.setInt(2, citt);
			stmt.setString(3,cittadinanza);
			stmt.setString(4, residenza);
			stmt.setString(5, via);
			stmt.setInt(6, numCiv);
			stmt.setString(7, statoCiv);
			stmt.setString(8, professione);
			stmt.setDouble(9, statura);
			stmt.setString(10, capelli);
			stmt.setString(11,occhi);
			stmt.setString(12, segniParticolari);
			stmt.setDate(13, new java.sql.Date(dataRilascio.getYear()-1900,dataRilascio.getMonth()-1,dataRilascio.getDate()));
			stmt.setDate(14, new java.sql.Date(dataScadenza.getYear()-1900,dataScadenza.getMonth()-1,dataScadenza.getDate()));
			stmt.setInt(15, esp);
			
			return (stmt.executeUpdate() == 1);
		}
		catch (SQLException exc)
		{
			throw new DbEccezione("Errore inserimento carta d'identit‡");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e1) 
			{
				throw new DbEccezione("Errore ricerca carta d'identit√† tramite il suo numero");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica della via in una specifica carta d'identit‡†. (aggiornamento del db)
	 * @param cod Ë il numero della carta d'identit‡† 
	 * @param v Ë la nuova via da registrare nella carta d'identit‡†
	 * @return true se l'operazione Ë eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaViaCartaIdentita (String cod, String v) throws DbEccezione
	{
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cartaidentita SET via = ? WHERE numero = ?");
			stmt.setString(1, v);
			stmt.setString(2, cod);
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica via carta d'identit√†");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore modifica via carta d'identit√†");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica del numero civico in una specifica carta d'identit‡†. (aggiornamento del db)
	 * @param cod Ë il numero della carta d'identit‡
	 * @param nc Ë il nuovo numero civico
	 * @return true se l'operazione Ë eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaNumeroCivicoCartaIdentita (String cod,int nc) throws DbEccezione
	{
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cartaidentita SET numeroCivico = ? WHERE numero = ?");
			stmt.setInt(1, nc);
			stmt.setString(2, cod);
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica numero civico carta d'identit√†");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore modifica numero civico carta d'identit√†");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica della residenza (via e numero civio) in una specifica carta d'identit‡†. (aggiornamento del db)†
	 * @param via Ë la nuova via da registrare nella carta d'identit‡†
	 * @param nc Ë il numero civico da registrare nella carta d'identit‡
	 * @return true se l'operazione Ë eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaResidenzaCartaIdentita (String cod, String via, int nc) throws DbEccezione
	{
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cartaidentita SET via = ?, numeroCivico = ? WHERE numero = ?");
			stmt.setString(1, via);
			stmt.setInt(2, nc);
			stmt.setString(3, cod);
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica residenza carta d'identit‡†");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore modifica residenza carta d'identit‡†");
			}
		}
	}

	/**
	 * Metodo che permette la modifica della data di rilascio di una specifica carta d'identit‡†. (aggiornamento del db)
	 * @param cod Ë il numero della carta d'identit‡†
	 * @param d Ë la nuova data di rilascio della carta d'identit‡†
	 * @return true se l'operazione Ë eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaDataRilascioCartaIdentita (String cod, java.util.Date d) throws DbEccezione
	{
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cartaidentita SET dataRilascio = ? WHERE numero = ?");
			stmt.setString(2, cod);
			stmt.setDate(1,new java.sql.Date(d.getYear()-1900,d.getMonth()-1,d.getDate()));
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione ("Errore modifica data rilascio carta d'identit√†");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione ("Errore modifica data rilascio carta d'identit√†");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica della data di scadenza per una specifica carta d'identit‡†. (aggiornamento del db)
	 * @param cod Ë il numero della carta d'identit‡†
	 * @param d Ë la nuova data di scadenza
	 * @return true se l'operazione Ë eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaDataScadenzaCartaIdentita (String cod, java.util.Date d) throws DbEccezione
	{
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cartaidentita SET dataScadenza = ? WHERE numero = ?");
			stmt.setString(2, cod);
			stmt.setDate(1,new java.sql.Date(d.getYear()-1900,d.getMonth()-1,d.getDate()));
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica data scadenza carta d'identit√†"); 
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore modifica data scadenza carta d'identit√†"); 
			}
		}	
	}
	
	/**
	 * Metodo che permette la modifica della validit‡†per l'espatrio di una specifica carta d'identit‡†. (aggiornamento del db)
	 * @param cod Ë il numero della carta d'identit‡†
	 * @param esp Ë il valore booleano che indica la validit‡ per l'espatrio per la specifica carta d'identit‡†
	 * @return true se l'operazione Ë eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaValidaEspatrio (String cod, boolean esp) throws DbEccezione
	{
		PreparedStatement stmt = null;
		int e;
		if (esp==true)
			e=1;
		else
			e=0;
		try
		{
			stmt = connection.prepareStatement("UPDATE cartaidentita SET validaEspatrio = ? WHERE numero = ?");
			stmt.setString(2, cod);
			stmt.setInt(1, e);
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica validit√† espatrio carta d'identit√†");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e1) 
			{
				throw new DbEccezione("Errore modifica validit√† espatrio carta d'identit√†");
			}
		}
	}	
    /**
     * Metodo che permette la ricerca di una carta d'identit‡ a partire dall'id del proprietario
     * @param idC Ë l'id del cittadino
     * @return l'oggetto di tipo CartaIdentita dello specifico cittadino.
     * @throws DbEccezione
     */
	public CartaIdentita ricercaCartaIdentitaPerProprietario (int idC) throws DbEccezione
	{	
		CartaIdentita res = null;
		ResultSet rs = null;
		PreparedStatement stmt = null;
		boolean e;
		try
		{
			stmt = connection.prepareStatement("SELECT * FROM cartaidentita WHERE cittadino = ?");
			stmt.setInt(1, idC);
			rs = stmt.executeQuery();
		if(rs.next()==true)
			{
				String num = rs.getString("numero");
				int citt = rs.getInt("cittadino");
				String cittadinanza = rs.getString("cittadinanza");
				String residenza =rs.getString("residenza");
				String via = rs.getString("via");
				int numciv = rs.getInt("numeroCivico");
				String statoCivile = rs.getString("statoCivile");
				String professione = rs.getString("professione");
				double statura = rs.getDouble("statura");
				String capelli = rs.getString("capelli");
				String occhi = rs.getString("occhi");
				String segniParticolari = rs.getString("segniParticolari");
				java.util.Date dataRilascio = rs.getDate("dataRilascio");
				java.util.Date dataScadenza = rs.getDate("dataScadenza");
				int esp = rs.getInt("validaEspatrio");
				if(esp == 1)
					e=true;
				else 
					e=false;
				res = new CartaIdentita(num,citt,cittadinanza,residenza,via,numciv,statoCivile,professione,statura,capelli,occhi,segniParticolari,dataRilascio,dataScadenza,e);
				}
			return res;
		}
		catch (SQLException exc)
		{
			throw new DbEccezione("Errore ricerca carta d'identit√† tramite id del cittadino");
		}
		finally
		{
			try 
			{
				if(rs!=null)
					rs.close();
				if(stmt!=null)
					stmt.close();
			} 
			catch (SQLException e1) 
			{
				throw new DbEccezione("Errore ricerca carta d'identit√† tramite id del cittadino");
			}
		}
	}

}
