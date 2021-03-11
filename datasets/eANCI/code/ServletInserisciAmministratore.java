package Servlet;

import java.io.IOException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import Manager.AccessoManager;
import Manager.AmministratoreManager;
import Bean.Accesso;
import Bean.Amministratore;
import DB.DbEccezione;
/**
 * La classe ServletInserisciAmministratore inserisce un amministratore nel database
 * La classe ServletInserisciAmministratore non ha dipendenze
 * @author Federico Cinque
 */
public class ServletInserisciAmministratore extends HttpServlet {
	private String nome;
	private String cognome;
	private String email;
	private String matricola;
	private String login;
	private String password;
	private String tipo;

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		HttpSession session = richiesta.getSession();

		if(session!=null){	//Se la sessione + nulla effettua il redirect alla pagina di autenticazione
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				nome = richiesta.getParameter("nome");
				cognome = richiesta.getParameter("cognome");
				email = richiesta.getParameter("email");
				matricola = richiesta.getParameter("matricola");
				login = richiesta.getParameter("login");
				password = richiesta.getParameter("password");
				tipo = richiesta.getParameter("tipo");

				AccessoManager AM = new AccessoManager();
				AmministratoreManager AdM = new AmministratoreManager();

				Accesso ac = new Accesso(login,password,tipo);
				Amministratore am = new Amministratore(nome,cognome,matricola,email,login);

				rd = null;
				sc = getServletContext();

				if(AM.inserisciAccesso(ac) && AdM.inserisciAdmin(am)){ //inserisco idati relativi all'accesso e all'amministratore
																		//controllando l'esito positivo
					ris="ok";
					richiesta.setAttribute("ris", ris);
					rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=riuscita"); 
				}
				else{
					ris="fallita";
					richiesta.setAttribute("ris", ris);
					rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
				}
				rd.forward(richiesta,risposta);
			}
			catch(DbEccezione e){
				ris=e.getMessage();
				richiesta.setAttribute("ris", ris);
				rd=sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
				rd.forward(richiesta,risposta);
			}
		}
		else{
			String url="/myDoc/workers/Accesso.jsp";
			risposta.sendRedirect(url);
		}
	}
}
