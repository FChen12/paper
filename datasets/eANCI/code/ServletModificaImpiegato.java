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
import Manager.ImpiegatoManager;
import Bean.Accesso;
import Bean.Impiegato;
import DB.DbEccezione;
/**
 * La classe ServletModificaImpiegato che effettua l'operazione di modifica di un impiegato
 * La classe ServletModificaImpiegato non ha dipendenze
 * @author Federico Cinque
 */
public class ServletModificaImpiegato extends HttpServlet{

	private String nome;
	private String cognome;
	private String email;
	private String matricola;
	private String login;
	private String password;
	private String tipo;

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		HttpSession session = richiesta.getSession();
		if(session!=null){	//Se la sessioneè nulla effettua il redirect alla pagina di autenticazione
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				//Se gli attributi di sessione amm e acc sono nulli devo effettuare la ricerca
				if(session.getAttribute("amm")==null && session.getAttribute("acc")==null){
					matricola = richiesta.getParameter("matricola");
					ImpiegatoManager IM = new ImpiegatoManager();
					Impiegato imp = IM.ricercaImpiegatoByMatricola(matricola);
					if(imp != null){
						session.setAttribute("amm", imp);

						AccessoManager AM = new AccessoManager();
						Accesso ac = AM.ottenereAccesso(imp.ottenereLogin());
						session.setAttribute("acc", ac);

						rd = sc.getRequestDispatcher("/workers/index.jsp?func=modifica&page=impiegato"); 
						rd.forward(richiesta,risposta);
					}
					else{
						ris="La matricola non corrisponde ad un impiegato";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=fallita"); 
						rd.forward(richiesta,risposta);
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
					ImpiegatoManager IM = new ImpiegatoManager();

					Accesso ac = new Accesso(login,password,tipo);
					Impiegato imp = new Impiegato(nome,cognome,matricola,email,login);
					Impiegato impOld = (Impiegato) session.getAttribute("amm");
					
					if(AM.modificaAccesso(impOld.ottenereLogin(), ac) && IM.modificaImpiegato(impOld.ottenereMatricola(), imp)){	//procedo con la modifica dei dati
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
					rd.forward(richiesta,risposta);
					session.removeAttribute("amm");
					session.removeAttribute("acc");
				}
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
