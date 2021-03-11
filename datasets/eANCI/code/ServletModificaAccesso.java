package Servlet;

import java.io.IOException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import Bean.Accesso;
import DB.DbEccezione;
import Manager.AccessoManager;
/**
 * La classe ServletModificaAccesso che effettua l'operazione di modifica di un accesso
 * La classe ServletModificaAccesso non ha dipendenze
 * @author Federico Cinque
 */
public class ServletModificaAccesso extends HttpServlet{

	private String login;
	private String password;
	private String cpassword;
	private String tipo;

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		HttpSession session = richiesta.getSession();

		if(session!=null){	//Se la sessione é nulla effettua il redirect alla pagina di autenticazione
			ServletContext sc = getServletContext();
			RequestDispatcher rd = null;
			String ris;
			try{
				login = richiesta.getParameter("login");
				password = richiesta.getParameter("password");
				cpassword = richiesta.getParameter("cpassword");
				tipo = richiesta.getParameter("tipo");

				AccessoManager AM = new AccessoManager();
				Accesso ac = new Accesso(login,password,tipo);

				if(AM.modificaAccesso(login, ac)){	//modifico i dati relativi all'accesso controllando che l'esito sia positivo
					ris="ok";
					richiesta.setAttribute("ris", ris);
					if(ac.ottenereTipo().equals("Cittadino"))
						rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=riuscita");
					else
						rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=riuscita"); 
				}
				else{
					ris="fallita";
					richiesta.setAttribute("ris", ris);
					if(ac.ottenereTipo().equals("Cittadino"))
						rd = sc.getRequestDispatcher("/user/home.jsp?func=operazione&page=fallita");
					else
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
		else{	//questa servlet viene invocata sia dal lato cittadino sia da amm/imp
				//quindi effettuo un controllo da quale url proviene la richiesta
				//cosi posso effettuare il redirect alla pagina corretta
			String from = richiesta.getRequestURL().toString();
			String url;
			if(from.contains("user"))
				url="/myDoc/user/home.jsp";
			else
				url="/myDoc/workers/Accesso.jsp";
			risposta.sendRedirect(url);
		}
	}
}
