package DB;
import java.sql.*;
import java.util.*;

import Bean.Cittadino;


/** 
 * Classe che si occupa di gestire le connessioni con il database
 *  e di schermare le servet con il DBMS.
 * 
 * @author Michelangelo Cianciulli
 */
public class DbCittadino 
{
	private Connection connection;
	
	public DbCittadino() throws DbEccezione
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
	 * Metodo che permette di registrare un nuovo cittadino. (aggiornamento del db)
	 * @param citt è l'istanza di cittadino
	 * @return l'id del cittadino inserito.
	 * @throws DbEccezione
	 */
	public int registraCittadino(Cittadino citt) throws DbEccezione
	{
		PreparedStatement stmt = null;
		int a;
		String login=citt.ottenereLogin();
		String cognome=citt.ottenereCognome();
		String nome=citt.ottenereNome();
		java.util.Date d=citt.ottenereDataNascita();
		String luogoN = citt.ottenereLuogoNascita();
		String codF=citt.ottenereCodiceFiscale();
		String email=citt.ottenereEmail();
		boolean adv=citt.isAdvertise();
		int nuclF=citt.ottenereNucleoFamiliare();
		if(adv==true)
			a=1;
		else a=0;
		try
		{
			
				stmt = connection.prepareStatement("INSERT INTO cittadino VALUES (?,?,?,?,?,?,?,?,?,?)");
				stmt.setInt(1, 0);
				stmt.setString(2, codF);
				stmt.setString(3, cognome);
				stmt.setString(4, nome);
				stmt.setDate(5, new java.sql.Date(d.getYear()-1900,d.getMonth()-1,d.getDate()));
				stmt.setString(6, luogoN);
				stmt.setString(7, email);
				stmt.setInt(8, a);
				if(nuclF!=0)
					stmt.setInt(9, nuclF);
				else
					stmt.setNull(9, java.sql.Types.NULL);
				stmt.setString(10, login);
				stmt.executeUpdate();
				return maxID();
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore inserimento nuovo cittadino");
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
				throw new DbEccezione("Errore inserimento nuovo cittadino");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica del nome di uno specifico cittadino. (aggiornamento del db)
	 * @param idCitt è l'identificativo del cittadino
	 * @param newname il nuovo nome da assegnare al cittadino
	 * @return true se l'operazione è eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaNomeCittadino (int idCitt,String nuovoNome) throws DbEccezione
	{	
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cittadino SET nome = ? WHERE idCittadino = ?");
			stmt.setInt(2, idCitt);
			stmt.setString(1, nuovoNome);
			return (stmt.executeUpdate()==1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica nome cittadino");
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
				throw new DbEccezione("Errore modifica nome cittadino");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica del cognome di uno specifico cittadino. (aggiornamento del db)
	 * @param idCitt è l'identificativo del cittadino
	 * @param newsurname è il nuovo cognome da assegnare al cittadino
	 * @return true se l'operazione è eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaCognomeCittadino(int idCitt,String nuovoCognome) throws DbEccezione
	{ 
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cittadino SET cognome = ? WHERE idCittadino = ?");
			stmt.setInt(2, idCitt);
			stmt.setString(1, nuovoCognome);
			return (stmt.executeUpdate()==1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica cognome cittadino");
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
				throw new DbEccezione("Errore modifica cognome cittadino");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica del codice fiscale di uno specifico cittadino. (aggiornamento del db)
	 * @param idCitt è l'identificativo del cittadino
	 * @param newcf è il nuovo codice fiscale da assegnare al cittadino
	 * @return true se l'operazione è eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaCodiceFiscaleCittadino(int idCitt,String newcf) throws DbEccezione
	{
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cittadino SET codicefiscale = ? WHERE idCittadino = ?");
			stmt.setInt(2, idCitt);
			stmt.setString(1, newcf);
			return (stmt.executeUpdate()==1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica codice fiscale cittadino");
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
				throw new DbEccezione("Errore modifica codice fiscale cittadino");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica dell'indirizzo e-mail di uno specifico cittadino. (aggiornamento del db)
	 * @param idCitt è l'identificativo del cittadino
	 * @param newmail è la nuova mail da assegnare al cittadino
	 * @return true se l'operazione è eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaEmailCittadino(int idCitt,String newmail)throws DbEccezione
	{		
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cittadino SET eMail = ? WHERE idCittadino = ?");
			stmt.setInt(2, idCitt);
			stmt.setString(1, newmail);
			return (stmt.executeUpdate()==1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica mail cittadino");
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
				throw new DbEccezione("Errore modifica mail cittadino");
			}
		}
	}
	
	/**
	 * Metodo che permette la modifica del campo advertise di uno specifico cittadino. (aggiornamento del db)
	 * @param idCitt è l'identificativo del cittadino
	 * @return true se l'operazione è eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaAdvertise(int idCitt) throws DbEccezione
	{
		PreparedStatement stmt = null;
		ResultSet rs = null;
		int ret;
		try
		{
			stmt = connection.prepareStatement("SELECT advertise FROM cittadino WHERE idCittadino = ?");
			Statement statement = connection.createStatement();
			stmt.setInt(1, idCitt);
			rs = stmt.executeQuery();
			rs.next();
			int adv = rs.getInt("advertise");
			if (adv == 0) 
				ret = statement.executeUpdate("UPDATE cittadino SET advertise = 1 WHERE idCittadino = "+idCitt);
			else	
				ret = statement.executeUpdate("UPDATE cittadino SET advertise = 0 WHERE idCittadino ="+idCitt);
		
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica advertise cittadino");
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
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore modifica advertise cittadino");
			}	
		}
	}
	
	/**
	 * Metodo che permette la cancellazione di un cittadino. (aggiornamento del db)
	 * @param idCitt è l'identificativo del cittadino
	 * @return true se l'operazione è eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean cancellaCittadino(int idCitt) throws DbEccezione
	{	
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("DELETE FROM cittadino WHERE idCittadino = ?");
			stmt.setInt(1, idCitt);
			return (stmt.executeUpdate()==1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore cancellazione cittadino");
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
				throw new DbEccezione("Errore cancellazione cittadino");
			}
		}
	}
	
	/**
	 * Metodo che permette la ricerca di un cittadino tramite il suo id.
	 * @param idCitt è l'identificativo del cittadino
	 * @return oggetto di tipo cittadino con id uguale a quello passato come parametro
	 * @throws DbEccezione
	 */
	public Cittadino ottenereCittadinoPerCodice(int idCitt) throws DbEccezione
	{
		Cittadino res = null;
		PreparedStatement stmt = null;
		ResultSet rs = null;
		try
		{
			stmt = connection.prepareStatement("SELECT * FROM cittadino WHERE idCittadino = ?");
			stmt.setInt(1, idCitt);
			rs = stmt.executeQuery();
			if(rs.next() == true)
				{
				boolean adv;
				int idCittadino = rs.getInt("idCittadino");
				String codiceFiscale = rs.getString("codiceFiscale");
				String cognome = rs.getString("cognome");
				String nome = rs.getString("nome");
				java.util.Date dataNascita = rs.getDate("dataNascita");
				String luogoN = rs.getString("luogoNascita");
				String eMail = rs.getString("eMail");
				int advertise = rs.getInt("advertise");
				int nucleoFamiliare = rs.getInt("nucleoFamiliare");
				String login = rs.getString("login");
				if(advertise == 1)
					adv=true;
				else 
					adv=false;
				res = new Cittadino(idCittadino,codiceFiscale,cognome,nome,dataNascita,luogoN,eMail,adv,nucleoFamiliare,login);
				}
			return res;
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore ricerca cittadino by codice");
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
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore ricerca cittadino by codice");
			}
		}
	}
	
	/**
	 * Metodo che permette la ricerca di un insieme di cittadini in base al loro nome e cognome.
	 * @param name parametro su cui effettuare la ricerca
	 * @param surname parametro su cui effettuare la ricerca
	 * @return una collection di cittadini con il nome e il cognome passato come parametro
	 * @throws DbEccezione
	 */
	public Collection<Cittadino> ottenereCittadinoPerNome(String nome_,String cognome_) throws DbEccezione
	{
		
		Collection<Cittadino> res = new ArrayList<Cittadino>();
		PreparedStatement stmt = null;
		ResultSet rs = null;
		boolean adv;
		try
		{
			stmt = connection.prepareStatement("SELECT * FROM cittadino WHERE nome = ? AND cognome = ?");
			stmt.setString(1, nome_);
			stmt.setString(2, cognome_);
			rs = stmt.executeQuery();
			while(rs.next())
			{
				int idCittadino = rs.getInt("idCittadino");
				String codiceFiscale = rs.getString("codiceFiscale");
				String cognome = rs.getString("cognome");
				String nome = rs.getString("nome");
				java.util.Date dataNascita = rs.getDate("dataNascita");
				String luogoN = rs.getString("luogoNascita");
				String eMail = rs.getString("eMail");
				int advertise = rs.getInt("advertise");
				int nucleoFamiliare = rs.getInt("nucleoFamiliare");
				String login = rs.getString("login");
				if(advertise == 1)
					adv=true;
				else adv=false;
					res.add(new Cittadino(idCittadino,codiceFiscale,cognome,nome,dataNascita,luogoN,eMail,adv,nucleoFamiliare,login));
			}
				return res;
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore ricerca cittadini tramite nome e cognome");
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
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore ricerca cittadini tramite nome e cognome");
			}
		}	
	}
	
	/**
	 * Metodo che permette la modifica della login per uno specifico cittadino. (aggiornamento del db)
	 * @param idC è l'id del cittadino
	 * @param newLogin è la nuova login del cittadino
	 * @return true se l'operazione è andata a buon fine
	 */
	public boolean modificaLogin(int idC, String nuovoLogin) throws DbEccezione
	{
		PreparedStatement stmt = null;
		ResultSet rs = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cittadino SET login = ? WHERE idCittadino = ?");
			stmt.setString(1, nuovoLogin);
			stmt.setInt(2, idC);
			//rs = stmt.executeQuery();
			/*if(rs.next())
				{
				String l = rs.getString("login");
				stmt = connection.prepareStatement("UPDATE accesso SET login = ? WHERE login = ?");
				stmt.setString(1, newLogin);
				stmt.setString(2, l);*/
				return (stmt.executeUpdate()==1);
				//}
		//return false;
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica login");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
				if(rs!=null)
					rs.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore modifica login");
			}
		}
	}
	
	/**
	 * Metodo che permette la ricerca di un cittadino tramite la sua login.
	 * @param log è la login in base alla quale si vuole effettuare la ricerca
	 * @return l'oggetto di tipo cittadino
	 * @throws DbEccezione
	 */
	public Cittadino ottenereCittadinoPerLogin (String log) throws DbEccezione
	{
		Cittadino res = null;
		PreparedStatement stmt = null;
		ResultSet rs = null;
		try
		{
			stmt = connection.prepareStatement("SELECT * FROM cittadino WHERE login = ?");
			stmt.setString(1, log);
			rs = stmt.executeQuery();
			if(rs.next() == true)
				{
				boolean adv;
				int idCittadino = rs.getInt("idCittadino");
				String codiceFiscale = rs.getString("codiceFiscale");
				String cognome = rs.getString("cognome");
				String nome = rs.getString("nome");
				java.util.Date dataNascita = rs.getDate("dataNascita");
				String luogoN = rs.getString("luogoNascita");
				String eMail = rs.getString("eMail");
				int advertise = rs.getInt("advertise");
				int nucleoFamiliare = rs.getInt("nucleoFamiliare");
				String login = rs.getString("login");
				if(advertise == 1)
					adv=true;
				else 
					adv=false;
				res = new Cittadino(idCittadino,codiceFiscale,cognome,nome,dataNascita,luogoN,eMail,adv,nucleoFamiliare,login);
				}
			return res;
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore ricerca cittadino by login");
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
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore ricerca cittadino by login");
			}
		}
	}
	
	/**
	 * Metodo privato che ritorna l'id dell'ultimo cittadino inserito.
	 * @return l'id più alto della tabella cittadino
	 * @throws DbEccezione
	 */
	private int maxID () throws DbEccezione
	{
		Statement stmt = null;
		ResultSet rs = null;
		try
		{
			stmt = connection.createStatement();
			rs = stmt.executeQuery("SELECT max(idCittadino) as m FROM cittadino;");
			if(rs.next())
				return rs.getInt("m");
			throw new DbEccezione("Errore esecuzione maxID");
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore esecuzione maxID");
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
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore esecuzione maxID");
			}	
		}
	}
	
	/**
	 * Metodo che permette di conoscere l'id del cittadino a partire dai suoi dati anagrafici (codice fiscale,cognome,nome)
	 * @param cf è il codice fiscale parametro per la ricerca
	 * @param surname è il cognome parametro per la ricerca
	 * @param name è il nome parametro per la ricerca
	 * @return l'id del cittadino se ok, -1 se la ricerca non ha successo
	 */
	public int trovaIdCittadino (String cf,String cognome,String nome)
	{	
		PreparedStatement stmt = null;
		ResultSet rs = null;
		try
		{
			stmt = connection.prepareStatement("SELECT idCittadino AS id FROM cittadino WHERE codiceFiscale = ? AND nome = ? AND cognome = ?");
			stmt.setString(1, cf);
			stmt.setString(2, nome);
			stmt.setString(3, cognome);
			rs = stmt.executeQuery();
			if(rs.next())
				return rs.getInt("id");
			return -1;
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore ricerca id cittadino tramite cf/nome/cognome");
		}
		finally
		{
			try 
			{
				if(stmt!=null)
					stmt.close();
				if(rs!=null)
					rs.close();
			} 
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore ricerca id cittadino tramite cf/nome/cognome");
			}
		}
	}
	
	/**
	 * Metodo che permette la ricerca del codice fiscale del cittadino a partire dal suo ID
	 * @param id è l'id del cittadino
	 * @return il codice fiscale del cittadino
	 */
	public String trovaCodiceFiscale (int id)
	{
		PreparedStatement stmt = null;
		ResultSet rs = null;
		String res = null;
		try
		{
			stmt = connection.prepareStatement("SELECT codiceFiscale as cf FROM cittadino WHERE idCittadino = ?");
			stmt.setInt(1, id);
			rs = stmt.executeQuery();
			if(rs.next())
				res = rs.getString("cf");
			return res;
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore ricerca codice fiscale tramite ID");
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
			catch (SQLException e) 
			{
				throw new DbEccezione("Errore ricerca codice fiscale tramite ID");
			}	
		}
	}
	
	/**
	 * Metodo che modifica il nucleo familiare del cittadino dato il suo id
	 * @param idCitt è l'id del cittadino
	 * @param newnucleo è il nuovo nucleo familiare del cittadino
	 * @return true se l'operazione è eseguita con successo
	 * @throws DbEccezione
	 */
	public boolean modificaNucleoFamiliareCittadino(int idCitt,int nuovoNucleo) throws DbEccezione
	{	
		PreparedStatement stmt = null;
		try
		{
			stmt = connection.prepareStatement("UPDATE cittadino SET nucleoFamiliare = ? WHERE idCittadino = ?");
			stmt.setInt(2, idCitt);
			stmt.setInt(1, nuovoNucleo);
			int ret = stmt.executeUpdate();
			return (ret == 1);
		}
		catch(SQLException exc)
		{
			throw new DbEccezione("Errore modifica nucleo familiare cittadino");
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
				throw new DbEccezione("Errore modifica nucleo familiare cittadino");
			}
		}
	}
}
