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
 * La classe ServletModificaAmministratore che effettua l'operazione di modifica di un amministratore
 * La classe ServletModificaAmministratore non ha dipendenze
 * @author Federico Cinque
 */
public class ServletModificaAmministratore extends HttpServlet{

	private String nome;
	private String cognome;
	private String email;
	private String matricola;
	private String login;
	private String password;
	private String tipo;

	public void doPost(HttpServletRequest richiesta,HttpServletResponse response) throws ServletException, IOException{
		HttpSession session = richiesta.getSession();
		if(session!=null){	//Se la sessione é nulla effettua il redirect alla pagina di autenticazione
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				//Se gli attributi di sessione amm e acc sono nulli devo effettuare la ricerca
				if(session.getAttribute("amm")==null && session.getAttribute("acc")==null){
					String matricola = richiesta.getParameter("matricola");
					AmministratoreManager AdM = new AmministratoreManager();
					Amministratore am = AdM.ricercaAdminByMatricola(matricola);
					if(am != null){
						session.setAttribute("amm", am);

						AccessoManager AM = new AccessoManager();
						Accesso ac = AM.ottenereAccesso(am.ottenereLogin());
						session.setAttribute("acc", ac);

						rd = sc.getRequestDispatcher("/workers/index.jsp?func=modifica&page=amministratore"); 
						rd.forward(richiesta,response);
					}
					else{
						ris="La matricola non corrisponde ad un amministratore";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita"); 
						rd.forward(richiesta,response);
					}
				}
				else{
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
					Amministratore amOld = (Amministratore) session.getAttribute("amm");
					
					if(AM.modificaAccesso(amOld.ottenereLogin(), ac) && AdM.modificaAdmin(amOld.ottenereMatricola(), am)){ //procedo con la modifica dei dati
						//controllando l'esito
						ris="ok";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=riuscita");
					}
					else{
						ris="fallita";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
					}
					rd.forward(richiesta,response);
					session.removeAttribute("amm");
					session.removeAttribute("acc");
				}
			}
			catch(DbEccezione e){
				ris=e.getMessage();
				richiesta.setAttribute("ris", ris);
				rd=sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita");
				rd.forward(richiesta,response);
			}
		}
		else{
			String url="/myDoc/workers/Accesso.jsp";
			response.sendRedirect(url);
		}
	}
}
