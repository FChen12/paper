package Servlet;

import java.io.IOException;
import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import Manager.AccessoManager;
import Manager.CIManager;
import Manager.CittadinoManager;
import Bean.Accesso;
import Bean.CartaIdentita;
import Bean.Cittadino;
import DB.DbEccezione;
/**
 * La classe ServletRegistraCittadino gestisce l'operazione di registrazione 
 * di un cittadino nel sistema
 * La classe ServletRegistraCittadino non ha dipendenze
 * @author Federico Cinque
 */
public class ServletRegistraCittadino extends HttpServlet  {
	private String nome;
	private String cognome;
	private String email;
	private String ci;
	private String cf;
	private String login;
	private String password;
	private String tipo;

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		RequestDispatcher rd = null;
		ServletContext sc = getServletContext();
		String ris;
		try{
			nome = richiesta.getParameter("nome");
			cognome = richiesta.getParameter("cognome");
			email = richiesta.getParameter("email");
			ci = richiesta.getParameter("ci");
			cf = richiesta.getParameter("cf").toUpperCase();
			login = richiesta.getParameter("login");
			password = richiesta.getParameter("password");
			tipo = "Cittadino";

			CittadinoManager CM = new CittadinoManager();
			CIManager CIM = new CIManager();
			AccessoManager AM = new AccessoManager();
			CartaIdentita CI = CIM.ottenereCartaPerNumero(ci);

			if(CI!=null){
				if(!AM.controllaLogin(login)){
					Accesso ac = new Accesso(login,password,tipo);
					Cittadino c = CM.ottenereCittadinoPerId(CI.id());
					if(c.ottenereCodiceFiscale().equals(cf) && c.ottenereCognome().equals(cognome) && c.ottenereNome().equals(nome)){
						if(AM.inserisciAccesso(ac) && CM.modificaLogin(c.ottenereIdCittadino(), login) && CM.modificaEmail(c.ottenereIdCittadino(), email)){
							ris="ok";
							richiesta.setAttribute("ris", ris);
							rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=riuscita");
						}
						else{
							ris="fallita";
							richiesta.setAttribute("ris", ris);
							rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
						}
					}
					else{
						ris="I dati inseriti non corrispondono";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
					}
				}
				else{
					ris="Siamo spiacenti, la login é giˆ presente";
					richiesta.setAttribute("ris", ris);
					rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
				}
			}
			else{
				ris="Siamo spiacenti, il codice della carta d'identitˆ noné presente nel database";
				richiesta.setAttribute("ris", ris);
				rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
			}
			rd.forward(richiesta,risposta);
		}
		catch(DbEccezione e){
			ris=e.getMessage();
			richiesta.setAttribute("ris", ris);
			rd=sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
			rd.forward(richiesta,risposta);
		}
	}
}
