package DB;
import Bean.*;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Collection;

/**
 * La classe DbNucleoFamiliare si occupa di gestire le connessioni al db
 * @author Antonio Leone
 * @version 1.0
 */
public class DbNucleoFamiliare {
	
	private Connection connection;
	
	public DbNucleoFamiliare() throws DbEccezione
	{
		try
		{
			connection=DbConnessione.ottenereConnection();
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: Connessione non riuscita");
		}
	}
	
	/**
	 * Metodo che inserisci un oggetto nucleoFamiliare nel db
	 * @param nf Oggetto di tipo nucleofamiliare
	 * @return Restituisce l'id del nucleo familiare inserito
	 * @throws DbEccezione
	 */
	public int inserisciNucleoFamiliare(NucleoFamiliare nf)throws DbEccezione
	{
		PreparedStatement statement=null;
		int idC=nf.ottenereCapoFamiglia();
		String note=nf.ottenereNote();
		int nc=nf.ottenereNComponenti();
		try
		{
			statement=connection.prepareStatement("INSERT INTO nucleofamiliare VALUES (? ,? ,?,?)");
			statement.setInt(1,0);
			statement.setInt(2, idC);
			statement.setString(3, note);
			statement.setInt(4,nc);
			statement.executeUpdate();
			return lastId();
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: inserimento nucleo familiare non riuscito");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: inserimento nucleo familiare non riuscito");
			}
		}
	}
	
	/**
	 * Metodo che elimina un nucleoFamiliare  dal db
	 * @param id l'intero che viene utilizzato come id del nucleoFamiliare
	 * @return True se è stato effettuato una cancellazione nel db, False altrimenti
	 * @throws DbEccezione
	 */
	public boolean eliminaNucleoFamiliare(int id)throws DbEccezione
	{
		PreparedStatement statement=null;
		int ret=0;
		try
		{
			statement=connection.prepareStatement("DELETE FROM nucleofamiliare WHERE idNucleoFamiliare =?");
			statement.setInt(1,id);
			ret= statement.executeUpdate();
			return (ret==1);
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: cancellazione nucleo familiare non riuscita");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: cancellazione nucleo familiare non riuscita");
			}
		}
	}
	
	/**
	 * Metodo che restituisce i componeneti di uno stato di famiglia
	 * @param id intero che viene usato come id del nucleo familiare
	 * @return Restituisce una Collection di cittadini
	 * @throws DbEccezione
	 */
	public Collection<Cittadino> ottenereStatoFamiglia(int id)throws DbEccezione
	{
		ArrayList<Cittadino> ret = new ArrayList<Cittadino>(); 
		PreparedStatement statement=null;
		ResultSet rs=null;
		NucleoFamiliare nf=ottenereNucleoFamiliarePerId(id);
		if(nf==null)
			return null;
		int nc=nf.ottenereNComponenti();
		try
		{
			statement=connection.prepareStatement("SELECT * FROM statofamiglia WHERE nucleoFamiliare = ?");
			statement.setInt(1,id);
			rs = statement.executeQuery();
			for(int i=0;i<nc;i++)
			{
				rs.next();
				String cc=rs.getString("codiceFiscale");
				String cognome = rs.getString("cognome");
				String nome = rs.getString("nome");
				java.util.Date dataNascita = rs.getDate("dataNascita");
				String luogo=rs.getString("luogoNascita");
				int nucleoFamiliare = rs.getInt("nucleoFamiliare");
				ret.add(new Cittadino(nucleoFamiliare,cc,cognome,nome,dataNascita,luogo));
			}
			if(ret.isEmpty())
				return null;
			else
				return ret;
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: ricerca stato famiglia non riuscita");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
				if(rs!=null)
					rs.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: ricerca stato famiglia non riuscita");
			}
		}
	}

	/**
	 * Metodo che permette di controllare l’esistenza di un nucleo familiare
	 * @param id l'intero che viene utilizzato come id del nucleo familiare
	 * @return True se l'id è presente, False altrimenti
	 * @throws DbEccezione 
	 */
	public boolean controllaIdFamiglia(int id)throws DbEccezione
	{
			PreparedStatement statement=null;
			ResultSet rs=null;
			boolean ret=false;
			try
			{
				statement=connection.prepareStatement("SELECT * FROM nucleofamiliare WHERE idNucleoFamiliare = ?");
				statement.setInt(1,id);
				rs= statement.executeQuery();
				ret=rs.next();
				return(ret);
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: controllo nucleo familiare non riuscito");
			}
			finally
			{
				try
				{
					if(statement!=null)
						statement.close();
					if(rs!=null)
						rs.close();
				}
				catch(SQLException e)
				{
					throw new DbEccezione("Errore: controllo nucleo familiare non riuscito");
				}
			}
	}
	
	/**
	 * Metodo che permette la ricerca di un nucleo familiare per conoscere le eventuali note
	 * @param id l'intero che viene utilizzato come id del nucleo familiare
	 * @return Restituisce le note del nucleo familiare
	 * @throws DbEccezione
	 */
	public String noteFamiglia (int id)throws DbEccezione
	{
		PreparedStatement statement =null;
		ResultSet rs=null;
		String ret="";
		try
		{
			statement=connection.prepareStatement("SELECT note FROM nucleofamiliare WHERE idNucleoFamiliare = ?");
			statement.setInt(1,id);
			rs= statement.executeQuery();
			if(!rs.next())
				return null;
			ret=rs.getString("note");
			if(ret==null)
				return "";
			else
				return ret;
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: ricerca note non riuscita");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
				if(rs!=null)
					rs.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: ricerca note non riuscita");
			}
		}
	}
	
	/**
	 * Metodo che modifica un capo famiglia
	 * @param idF l'intero che viene utilizzato come id della famiglia
	 * @param idC l'intero che viene utilizzato come id del capo famiglia
	 * @return True se la modifica ha avuto successo, altrimenti False
	 * @throws DbEccezione
	 */
	public boolean settareCapoFamiglia(int idF,int idC)throws DbEccezione
	{
		PreparedStatement statement=null;
		int ret=0;
		try
		{
			statement=connection.prepareStatement("UPDATE nucleofamiliare SET capoFamiglia = ? WHERE idNucleoFamiliare = ?");
			statement.setInt(1,idC);
			statement.setInt(2,idF);
			ret= statement.executeUpdate();
			return (ret==1);
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: modifica capo famiglia non riuscita");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: modifica capo famiglia non riuscita");
			}
		}
	}
	
	/**
	 * Metodo che restituisce un nucleo familiare
	 * @param id l'intero che contiene l'id del nucleo familiare
	 * @return Restituisce un oggetto di tipo NucleoFamiliare
	 * @throws DbEccezione
	 */
	public NucleoFamiliare ottenereNucleoFamiliarePerId(int id)throws DbEccezione
	{
		PreparedStatement statement=null;
		ResultSet rs=null;
		NucleoFamiliare ret=null;
		try
		{
			statement=connection.prepareStatement("SELECT* FROM nucleofamiliare WHERE idNucleoFamiliare = ?");
			statement.setInt(1,id);
			rs= statement.executeQuery();
			if(!rs.next())
				return ret;
			int idN=rs.getInt("idNucleoFamiliare");
			int idC=rs.getInt("capoFamiglia");
			String note=rs.getString("note");
			int nc=rs.getInt("nComponenti");
			ret=new NucleoFamiliare(idN,idC,note,nc);
			return ret;
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: ricerca nucleo familiare tramite id non riuscito");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
				if(rs!=null)
					rs.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: ricerca nucleo familiare tramite id non riuscito");
			}
		}
	}

	private int lastId()throws DbEccezione
	{	
		int ret=0;
		Statement statement=null;
		ResultSet rs=null;
		try
		{
			statement=connection.createStatement();
			rs=statement.executeQuery("SELECT max(idNucleoFamiliare)AS max FROM nucleofamiliare");
			if(!rs.next())
				return ret;
			ret=rs.getInt(1);
			return ret;
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: ricerca id dell'ultimo nucleo familiare non riuscito");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
				if(rs!=null)
					rs.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: ricerca id dell'ultimo nucleo familiare non riuscito");
			}
		}
	}
	
	/**
	 * Metodo che modifica il numero di componenti del nucleo familiare
	 * @param idF l'intero che viene utilizzato come id della famiglia
	 * @param n l'intero che rappresenta il nuovo numero di componenti
	 * @return True se la modifica ha avuto successo, altrimenti False
	 * @throws DbEccezione
	 */
	public boolean settareNComponenti(int idF,int n)
	{
		PreparedStatement statement=null;
		int ret=0;
		try
		{
			statement=connection.prepareStatement("UPDATE nucleofamiliare SET nComponenti = ? WHERE idNucleoFamiliare = ?");
			statement.setInt(1,n);
			statement.setInt(2,idF);
			ret= statement.executeUpdate();
			return (ret==1);
		}
		catch(SQLException e)
		{
			throw new DbEccezione("Errore: modifica numero componenti non riuscita");
		}
		finally
		{
			try
			{
				if(statement!=null)
					statement.close();
			}
			catch(SQLException e)
			{
				throw new DbEccezione("Errore: modifica numero componenti non riuscita");
			}
		}
	}
	
}