package Servlet;

import java.io.IOException;
import java.util.Random;
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
 * La classe ServletRecuperoPassword gestisce l'operazione di recupero password per un cittadino
 * La classe ServletRecuperoPassword non ha dipendenze
 * @author Federico Cinque
 */
public class ServletRecuperoPassword extends HttpServlet{

	private String email;
	private String ci;
	private String login;
	private String tipo;

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		RequestDispatcher rd = null;
		ServletContext sc = getServletContext();
		String ris;

		try{
			ci = richiesta.getParameter("ci").toUpperCase();
			login = richiesta.getParameter("login");
			tipo = "Cittadino";

			CittadinoManager CM = new CittadinoManager();
			CIManager CIM = new CIManager();
			AccessoManager AM = new AccessoManager();
			CartaIdentita CI = CIM.ottenereCartaPerNumero(ci);

			if(CI!=null){
				if(AM.controllaLogin(login)){
					Accesso ac = AM.ottenereAccesso(login);
					Cittadino c = CM.ottenereCittadinoPerId(CI.id());
					if(c.ottenereLogin().equals(login)){
						String p = generaPassword();	//nuova password auto-generata
						ac.settarePassword(p);
						AM.modificaAccesso(login, ac);

						//inviare l'email a c.getEmail();

						ris="E' stata inviata un email al suo indirizzo di posta elettronica";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=riuscita");
					}
					else{
						ris="La login non corrisponde alla codice della carta";
						richiesta.setAttribute("ris", ris);
						rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
					}
				}
				else{
					ris="Siamo spiacenti, la login nonè presente";
					richiesta.setAttribute("ris", ris);
					rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
				}
			}
			else{
				ris="Siamo spiacenti, il codice della carta d'identitˆ nonè presente nel database";
				richiesta.setAttribute("ris", ris);
				rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
			}
			rd.forward(richiesta,risposta);
		}
		catch(DbEccezione e){
			ris=e.getMessage();
			richiesta.setAttribute("ris", ris);
			rd=sc.getRequestDispatcher("/user/index.jsp?func=operazione&page=fallita");
			rd.forward(richiesta,risposta);
		}
	}


	private static String generaPassword() {
		String pass="";
		Random r = new Random();
		for(int i=0;i<8;i++){
			int x = r.nextInt(10);   // genera un intero tra 0 e 9
			char c = (char) ((int) 'A' + r.nextInt(26));   // genera un char tra 'A' e 'Z
			boolean s = r.nextBoolean();
			if(s)
				pass=pass+c;
			else
				pass=pass+x;
		}
		return pass;
	}

}
