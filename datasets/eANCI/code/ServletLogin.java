package Servlet;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import Manager.AccessoManager;
import Manager.AmministratoreManager;
import Manager.CIManager;
import Bean.Accesso;
import Bean.Amministratore;
import Bean.CartaIdentita;
import Bean.Cittadino;
import Manager.CittadinoManager;
import Bean.Impiegato;
import DB.DbEccezione;
import Manager.ImpiegatoManager;
/**
 * La classe ServletLogin effettua l'operazione di autenticazione di un utente nel sistema
 * La classe ServletLogin non ha dipendenze
 * @author Federico Cinque
 */
public class ServletLogin extends HttpServlet {

	public void doPost(HttpServletRequest richiesta,HttpServletResponse risposta) throws ServletException, IOException {
		int flag = -1;
		String login = richiesta.getParameter("login");
		String password = richiesta.getParameter("password");
		String tipo = richiesta.getParameter("tipo");

		HttpSession session = richiesta.getSession(true);
		try{
			AccessoManager AM = new AccessoManager();
			String url;

			Accesso ac = AM.ottenereAccesso(login);

			if(tipo!=null){	//Se tipo  diverso da null la servlet  stata invocata dal lato cittadino
				flag=0;
				if (AM.controllaAccesso(login, password) && ac.ottenereTipo().equals("Cittadino")){

					CittadinoManager CM = new CittadinoManager();
					Cittadino c = CM.ottenereCittadinoPerLogin(login);
					CIManager ciM=new CIManager();
					CartaIdentita ci=ciM.ottenereCartaPerIdCStri(c.ottenereIdCittadino());
					session.setAttribute("c", c);
					session.setAttribute("ci", ci);
					url="/myDoc/user/home.jsp";
				}
				else
					url="/myDoc/user/home.jsp?error=e";
			}
			else{	//Se tipo  null la servlet  stata invocata dal lato amministratore/impiegato
				flag = 1;
				if (AM.controllaAccesso(login, password) && !ac.ottenereTipo().equals("Cittadino")){
					session.setAttribute("login", ac.ottenereLogin());
					session.setAttribute("tipo", ac.ottenereTipo());
					if(ac.ottenereTipo().equals("Impiegato")){
						ImpiegatoManager IM = new ImpiegatoManager();
						Impiegato imp = IM.ottenereImpiegatoPerLogin(login);
						session.setAttribute("imp", imp);
					}
					else
						if(ac.ottenereTipo().equals("Amministratore")){
							AmministratoreManager AdM = new AmministratoreManager();
							Amministratore am = AdM.ottenereAmministratorePerLogin(login);
							session.setAttribute("am", am);
						}
					url="/myDoc/workers/index.jsp";
				}
				else
					url="/myDoc/workers/Accesso.jsp?error=e";
			}
			risposta.sendRedirect(url);
		}
		catch(DbEccezione e){
			String url;
			if(flag==1)
				url="/myDoc/workers/Accesso.jsp?error="+e.getMessage();
			else
				url="/myDoc/user/home.jsp?error="+e.getMessage();
			risposta.sendRedirect(url);
		}
	}
}