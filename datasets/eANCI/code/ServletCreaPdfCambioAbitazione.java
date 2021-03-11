package Servlet;
import Bean.CartaIdentita;
import Bean.Cittadino;
import DB.*;
import Manager.AccessoManager;
import Manager.CittadinoManager;
import Manager.NucleoFamiliareManager;

import java.io.*;
import java.util.GregorianCalendar;
import javax.servlet.*;
import javax.servlet.http.*;

import com.lowagie.text.Document;
import com.lowagie.text.DocumentException;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.PdfPCell;
import com.lowagie.text.pdf.PdfPTable;
import com.lowagie.text.pdf.PdfWriter;

/**
 * La classe ServletCreaPdfCambioAbitazione un file PDF in base ai dati ricevuti da una pagina JSP
 * La classe non ha nessuna dipendenza
 * @author Christian Ronca
 */


public class ServletCreaPdfCambioAbitazione extends HttpServlet {
	private static final long serialVersionUID = -168526506138896791L;
	private HttpSession session;
	
	public void doPost(HttpServletRequest richiesta, HttpServletResponse risposta) 
		throws ServletException, IOException {
		session = richiesta.getSession();
		
		try {
			GregorianCalendar gc = new GregorianCalendar();
			int gg = gc.get(GregorianCalendar.DATE);
			int mm = gc.get(GregorianCalendar.MONTH) + 1;
			int year = gc.get(GregorianCalendar.YEAR);
			String now = "" + year + mm + gg;
			String inout = "";
			
			String nome_comune			= richiesta.getParameter("comunename").toUpperCase();
			//String numb_document		= richiesta.getParameter("numberdocument");
			String nome					= richiesta.getParameter("name").toUpperCase();
			String surname				= richiesta.getParameter("surname").toUpperCase();
			String name_citta			= richiesta.getParameter("citta").toUpperCase();
			String gg_date				= richiesta.getParameter("gg");
			String mm_date				= richiesta.getParameter("mm");
			String aa_date				= richiesta.getParameter("aa");
			String newcomune			= richiesta.getParameter("newcomune").toUpperCase();
			String indir				= richiesta.getParameter("via").toUpperCase();
			String numero_civico		= richiesta.getParameter("civico");
			//String interno				= richiesta.getParameter("interno");
			String indirnew				= richiesta.getParameter("newvia").toUpperCase();
			String num_civnew			= richiesta.getParameter("num");
			//String interno_new			= richiesta.getParameter("interno1");
			String pref					= richiesta.getParameter("pref");
			String tel					= richiesta.getParameter("tel");
			String cntlr				= richiesta.getParameter("radio");
			String check				= richiesta.getParameter("check");
			
			String parent1				= richiesta.getParameter("parentela1").toUpperCase();
			String surname1				= richiesta.getParameter("surname1").toUpperCase();
			String name1				= richiesta.getParameter("name1").toUpperCase();
			String luogo1				= richiesta.getParameter("luogo1").toUpperCase();
			String gg1					= richiesta.getParameter("gg1");
			String mm1					= richiesta.getParameter("mm1");
			String aa1					= richiesta.getParameter("aa1");
			String parent2				= richiesta.getParameter("parentela2").toUpperCase();
			String surname2				= richiesta.getParameter("surname2").toUpperCase();
			String name2				= richiesta.getParameter("name2").toUpperCase();
			String luogo2				= richiesta.getParameter("luogo2").toUpperCase();
			String gg2					= richiesta.getParameter("gg2");
			String mm2					= richiesta.getParameter("mm2");
			String aa2					= richiesta.getParameter("aa2");
			String parent3				= richiesta.getParameter("parentela3").toUpperCase();
			String surname3				= richiesta.getParameter("surname3").toUpperCase();
			String name3				= richiesta.getParameter("name3").toUpperCase();
			String luogo3				= richiesta.getParameter("luogo3").toUpperCase();
			String gg3					= richiesta.getParameter("gg3");
			String mm3					= richiesta.getParameter("mm3");
			String aa3					= richiesta.getParameter("aa3");
			String parent4				= richiesta.getParameter("parentela4").toUpperCase();
			String surname4				= richiesta.getParameter("surname4").toUpperCase();
			String name4				= richiesta.getParameter("name4").toUpperCase();
			String luogo4				= richiesta.getParameter("luogo4").toUpperCase();
			String gg4					= richiesta.getParameter("gg4");
			String mm4					= richiesta.getParameter("mm4");
			String aa4					= richiesta.getParameter("aa4");
			String parent5				= richiesta.getParameter("parentela5").toUpperCase();
			String surname5				= richiesta.getParameter("surname5").toUpperCase();
			String name5				= richiesta.getParameter("name5").toUpperCase();
			String luogo5				= richiesta.getParameter("luogo5").toUpperCase();
			String gg5					= richiesta.getParameter("gg5");
			String mm5					= richiesta.getParameter("mm5");
			String aa5					= richiesta.getParameter("aa5");
			String parent6				= richiesta.getParameter("parentela6").toUpperCase();
			String surname6				= richiesta.getParameter("surname6").toUpperCase();
			String name6				= richiesta.getParameter("name6").toUpperCase();
			String luogo6				= richiesta.getParameter("luogo6").toUpperCase();
			String gg6					= richiesta.getParameter("gg6");
			String mm6					= richiesta.getParameter("mm6");
			String aa6					= richiesta.getParameter("aa6");
			
			String nome11				= richiesta.getParameter("nome11").toUpperCase();
			String nome12				= richiesta.getParameter("nome12").toUpperCase();
			String rapporto				= richiesta.getParameter("rapporto").toUpperCase();
			//String data_gg				= richiesta.getParameter("data_gg");
			//String data_mm				= richiesta.getParameter("data_mm");
			//String data_aa				= richiesta.getParameter("data_aa");
			//String identita1			= richiesta.getParameter("identita1").toUpperCase();
			//String identita2			= richiesta.getParameter("identita2").toUpperCase();
			//String cod_doc				= richiesta.getParameter("cod_document");
			String indirizzo			= richiesta.getParameter("indirizzo").toUpperCase();
			String num_civico1			= richiesta.getParameter("num_civico1");
			//String interno1				= richiesta.getParameter("interno1");
			String prec_res				= richiesta.getParameter("prec_res").toUpperCase();
			//String cc_date				= richiesta.getParameter("cc_date");
			//String cc_mese				= richiesta.getParameter("cc_mese");
			//String cc_anno				= richiesta.getParameter("cc_anno");
			String ab_libera			= richiesta.getParameter("abitaz");
			String abilita_cod_doc		= richiesta.getParameter("cod_doc");
			String cod_documento		= richiesta.getParameter("cod_documento");
			String nametab1				= richiesta.getParameter("nametab1").toUpperCase();
			String surnametab1			= richiesta.getParameter("surnametab1").toUpperCase();
			String nametab2				= richiesta.getParameter("nametab2").toUpperCase();
			String surnametab2			= richiesta.getParameter("surnametab2").toUpperCase();
			String nametab3				= richiesta.getParameter("nametab3").toUpperCase();
			String surnametab3			= richiesta.getParameter("surnametab3").toUpperCase();
			String nametab4				= richiesta.getParameter("nametab4").toUpperCase();
			String surnametab4			= richiesta.getParameter("surnametab4").toUpperCase();
			String nametab5				= richiesta.getParameter("nametab5").toUpperCase();
			String surnametab5			= richiesta.getParameter("surnametab5").toUpperCase();
			String nametab6				= richiesta.getParameter("nametab6").toUpperCase();
			String surnametab6			= richiesta.getParameter("surnametab6").toUpperCase();
			String nametab7				= richiesta.getParameter("nametab7").toUpperCase();
			String surnametab7			= richiesta.getParameter("surnametab7").toUpperCase();
			//String nametab8				= richiesta.getParameter("nametab8").toUpperCase();
			//String surnametab8			= richiesta.getParameter("surnametab8").toUpperCase();
			
			//String qualifica_vigile 	= richiesta.getParameter("qualifica_vigile"); //maresciallo
			String dati_vigile			= richiesta.getParameter("nome_vigile") + " " + richiesta.getParameter("cognome_vigile");
			String dispone				= richiesta.getParameter("testo_ufficiale");
			String accert				= richiesta.getParameter("text_area");
			String indirizzo_esatto_d	= richiesta.getParameter("radio1");
			String indirizzo_esatto		= richiesta.getParameter("indix"); // indix
			//String ab_effettivamente	= richiesta.getParameter("check");
			String alloggio_occupato	= richiesta.getParameter("check1");
			String cp1					= richiesta.getParameter("cogn_pers");
			String np1					= richiesta.getParameter("nome_pers");
			String pp1					= richiesta.getParameter("parent");
			String cp2					= richiesta.getParameter("cogn_pers1");
			String np2					= richiesta.getParameter("nome_pers1");
			String pp2					= richiesta.getParameter("parent1");
			String cp3					= richiesta.getParameter("cogn_pers2");
			String np3					= richiesta.getParameter("nome_pers2");
			String pp3					= richiesta.getParameter("parent2");
			String proprieta_componenti = richiesta.getParameter("check2");
			String titolo_di_possesso	= richiesta.getParameter("locazione");
			//String extra_possesso		= richiesta.getParameter("specification");
			String tipo_di_alloggio		= richiesta.getParameter("check3_si");
			String osser_abitazione		= richiesta.getParameter("textarea");
			String mot					= richiesta.getParameter("rad");
			String mot_causa			= richiesta.getParameter("text_trasfert");
			String professione			= richiesta.getParameter("prof1");
			String ind_lavoro			= richiesta.getParameter("all");
			String transfer				= richiesta.getParameter("indiconiuge");
			String circostanze			= richiesta.getParameter("circos");
			String oss_finali			= richiesta.getParameter("osservtext");
			
			cntlr = "stesso";
			if(cntlr.equals("stesso")) {
				inout = "interno";
			} else {
				inout = "altro";
			}
			
			Document document = new Document(PageSize.A4);
			PdfWriter.getInstance(document, risposta.getOutputStream());
			FileOutputStream fout = new FileOutputStream("webapps//myDoc//workers//pratiche_complete//" + now +"_2345_" + inout +".pdf");
			PdfWriter.getInstance(document, fout);
			risposta.setContentType("application/pdf");
			document.open();
			
			Paragraph spazio = new Paragraph("\n");
			Paragraph anagrafe_comune = new Paragraph("Anagrafe del comune di " + nome_comune, new Font(Font.HELVETICA, 10, Font.BOLD));
			anagrafe_comune.setAlignment(Element.ALIGN_RIGHT);
			document.add(anagrafe_comune);
			
			Paragraph oggetto = new Paragraph("OGGETTO: DICHIARAZIONE DI CAMBIAMENTO DI ABITAZIONE", new Font(Font.HELVETICA, 12, Font.BOLD));
			oggetto.setAlignment(Element.ALIGN_CENTER);
			document.add(oggetto);
			
			Paragraph sottoscritto = new Paragraph("   Io sottoscritto/a " + surname + " " + nome + " nato/a in " + name_citta +" il " + gg_date+"/"+mm_date+"/"+aa_date + 
					" già residente in via " + indir +" "+ numero_civico + " dichiaro, ai sensi e per gli effetti del combinato disposto dagli articoli 10," +
					" lettera a) e 13 del D.P.R. 30/05/1989, n 223 di essermi trasferito nel comune di "+ newcomune +" in via " + indirnew + " " +num_civnew + " tel: " + pref + " " + tel +
					" unitamente ai seguenti familiari/conviventi:\n ");
			sottoscritto.setAlignment(Element.ALIGN_JUSTIFIED);
			document.add(sottoscritto);
			
			//tabella stato di famiglia
			PdfPTable sf = new PdfPTable(5);
			sf.setWidthPercentage(100);
			sf.addCell(new Paragraph("PARENTELA"));
			sf.addCell(new Paragraph("NOME"));
			sf.addCell(new Paragraph("COGNOME"));
			sf.addCell(new Paragraph("LUOGO DI NASCITA"));
			sf.addCell(new Paragraph("DATA"));
			sf.addCell(new Paragraph(parent1));
			sf.addCell(new Paragraph(surname1));
			sf.addCell(new Paragraph(name1));
			sf.addCell(new Paragraph(luogo1));
			sf.addCell(new Paragraph(gg1+"/"+mm1+"/"+aa1));
			sf.addCell(new Paragraph(parent2));
			sf.addCell(new Paragraph(surname2));
			sf.addCell(new Paragraph(name2));
			sf.addCell(new Paragraph(luogo2));
			sf.addCell(new Paragraph(gg2+"/"+mm2+"/"+aa2));
			document.add(sf);
			
			Paragraph mendace = new Paragraph("Dichiaro, ai sensi e per gli effetti di cui art. 46 e 47 del DPR 445/00 e pienamente consapevole " +
					"delle responsabilità civili e penali previste in caso di dichiarazione mendace che:\n\n");
			mendace.setAlignment(Element.ALIGN_JUSTIFIED);
			document.add(mendace);
			
			if(ab_libera.equals("si")) {
				Paragraph ab = new Paragraph(" - l'abitazione nella quale mi sono trasferito/a è libera da persone e/o cose;\n\n\n");
				document.add(ab);
			} else {
				Paragraph occ = new Paragraph(" - è occupata da terze parti, sotto riportate: \n\n");
				document.add(occ);
				PdfPTable altri_occupanti = new PdfPTable(2);
				altri_occupanti.setWidthPercentage(100);
				altri_occupanti.addCell(new Paragraph("NOME"));
				altri_occupanti.addCell(new Paragraph("COGNOME"));
				altri_occupanti.addCell(new Paragraph(nametab1));
				altri_occupanti.addCell(new Paragraph(surnametab1));
				altri_occupanti.addCell(new Paragraph(nametab2));
				altri_occupanti.addCell(new Paragraph(surnametab2));
				altri_occupanti.addCell(new Paragraph(nametab3));
				altri_occupanti.addCell(new Paragraph(surnametab3));
				altri_occupanti.addCell(new Paragraph(nametab4));
				altri_occupanti.addCell(new Paragraph(surnametab4));
				altri_occupanti.addCell(new Paragraph(nametab5));
				altri_occupanti.addCell(new Paragraph(surnametab5));
				altri_occupanti.addCell(new Paragraph(nametab6));
				altri_occupanti.addCell(new Paragraph(surnametab6));
				altri_occupanti.addCell(new Paragraph(nametab7));
				altri_occupanti.addCell(new Paragraph(surnametab7));
				document.add(altri_occupanti);
				
				if(check != null) {
					Paragraph p = new Paragraph("\nche tra il/la Sig./ra " + nome11 + " ed il/la Sig./ra " + nome12 +" sussiste il seguente rapporto di: " +rapporto + "\n\n");
					document.add(p);
				} else {
					Paragraph p1 = new Paragraph("\nche non sussiste nessun rapporto di parentela con le persoche che occupano già l'alloggio e quelle che vi sono trasferite\n\n");
					document.add(p1);
				}
			}
					//inserire le altri info in caso di abilitazione

			

			Paragraph sdata = new Paragraph("Data: "+gg+"/"+mm+"/"+year, new Font(Font.HELVETICA, 12, Font.NORMAL));
			sdata.setAlignment(Element.ALIGN_LEFT);
			document.add(sdata);
			
			Paragraph firma_dichiarante = new Paragraph("_________________\nFirma del dichiarante\n\n", new Font(Font.HELVETICA, 12, Font.NORMAL));
			firma_dichiarante.setAlignment(Element.ALIGN_RIGHT);
			document.add(firma_dichiarante);
			
			if(abilita_cod_doc != null) {
				PdfPTable tabella_estremi = new PdfPTable(1);
				tabella_estremi.setWidthPercentage(100);
				PdfPCell cella = new PdfPCell();
				Paragraph livello = new Paragraph("(1) " + cod_documento);
				Paragraph livello2 = new Paragraph("In questo spazio riportare gli estremi del documento qualora la persona non sia conosciuta dall'ufficiale d'anagrafe.", new Font(Font.HELVETICA, 8));
				cella.addElement(livello);
				cella.addElement(livello2);
				tabella_estremi.addCell(cella);
				document.add(tabella_estremi);
			}
			
			Paragraph polizia = new Paragraph("\nAL COMANDO DI POLIZIA MUNICIPALE - SEDE", new Font(Font.HELVETICA, 12, Font.BOLD));
			polizia.setAlignment(Element.ALIGN_RIGHT);
			document.add(polizia);
			
			Paragraph alcomando_testo = new Paragraph("\n          A norma dell'art. 4 della legge n. 1228 e dell'art. 18, 1° comma del regolamento di esecuzione (DPR 30 maggio 1989, n. 223), pregasi assumere," +
					" tutte le informazioni riferite alle sopra elencate persone, rispondendo a tutte le domande indicate all' interno del presente foglio.\nDimora abituale dichiata in via "+indirizzo+ " " +num_civico1+
					"\nPrecedente residenza " + prec_res + "\n\n");
			alcomando_testo.setAlignment(Element.ALIGN_JUSTIFIED);
			document.add(alcomando_testo);
			document.add(sdata);
			
			Paragraph firma_impiegato = new Paragraph("_________________\nL'ufficiale di anagrafe responsabile\n\n", new Font(Font.HELVETICA, 12, Font.NORMAL));
			firma_impiegato.setAlignment(Element.ALIGN_RIGHT);
			document.add(firma_impiegato);
			
			Paragraph ufficiale_anagrafe = new Paragraph("L'UFFICIALE DI ANAGRAFE", new Font(Font.HELVETICA, 12, Font.BOLD));
			ufficiale_anagrafe.setAlignment(Element.ALIGN_CENTER);
			document.add(ufficiale_anagrafe);
			
			Paragraph ufficiale_testo = new Paragraph("Visto la relazione del Comando di Polizia Municipale\nA norma di: " + dati_vigile);
			document.add(ufficiale_testo);
			
			Paragraph disp = new Paragraph("DISPONE: " + dispone);
			document.add(disp);
			
			Paragraph testo_disp = new Paragraph("\n");
			testo_disp.setAlignment(Element.ALIGN_JUSTIFIED);
			document.add(testo_disp);
			document.add(sdata);
			document.add(firma_impiegato);
			
			Paragraph accertamento = new Paragraph("Accertamento del " + accert + "\n", new Font(Font.HELVETICA, 12, Font.BOLD));
			document.add(accertamento);
			Paragraph indirizzo_dic = new Paragraph(" - L'indirizzo dichiarato è esatto? " + indirizzo_esatto_d.toUpperCase() + "\n",
					new Font(Font.HELVETICA, 12, Font.COURIER));
			document.add(indirizzo_dic);
			if(indirizzo_esatto_d.equals("no")) {
				Paragraph indirizzo_es = new Paragraph(" - L'indirizzo esatto è: " + indirizzo_esatto.toUpperCase() + "\n");
				document.add(indirizzo_es);
			}
			
			
			Paragraph abitazione_eff = new Paragraph(" - La persona o le persone sopra citate abitano effettivamente all'indirizzo dichiarato? " + indirizzo_esatto_d.toUpperCase() + "\n");
			document.add(abitazione_eff);
			Paragraph alloggio_occ = new Paragraph(" - L'alloggio è occupato anche da altre persone residenti oltre quelle sopra citatate? " + alloggio_occupato.toUpperCase() +"\n");
			document.add(alloggio_occ);
			if(alloggio_occupato.equals("si")) {
				document.add(spazio);
				PdfPTable tabella_famiglia = new PdfPTable(3);
				tabella_famiglia.addCell(new Paragraph("COGNOME"));
				tabella_famiglia.addCell(new Paragraph("NOME"));
				tabella_famiglia.addCell(new Paragraph("RELAZIONE DI PARENTELA"));
				tabella_famiglia.addCell(new Paragraph(cp1));
				tabella_famiglia.addCell(new Paragraph(np1));
				tabella_famiglia.addCell(new Paragraph(pp1));
				tabella_famiglia.addCell(new Paragraph(cp2));
				tabella_famiglia.addCell(new Paragraph(np2));
				tabella_famiglia.addCell(new Paragraph(pp2));
				tabella_famiglia.addCell(new Paragraph(cp3));
				tabella_famiglia.addCell(new Paragraph(np3));
				tabella_famiglia.addCell(new Paragraph(pp3));
				tabella_famiglia.setWidthPercentage(100);
				document.add(tabella_famiglia);
			}
			
			Paragraph titolo = new Paragraph(" - L'alloggio è di proprietà di uno dei componenti? " + proprieta_componenti.toUpperCase() + "\n");
			document.add(titolo);
			if(proprieta_componenti.equals("no")) {
				Paragraph poss = new Paragraph(" - Titolo di possesso: " + titolo_di_possesso.toUpperCase() + "\n");
				document.add(poss);
			}
			
			Paragraph tipo_alloggio = new Paragraph(" - Tipo di alloggio: "+tipo_di_alloggio.toUpperCase() +"\n"); // inserire il tipo di alloggio
			document.add(tipo_alloggio);
			if(tipo_di_alloggio.equals("altro")) {
				Paragraph osservazioni_tipo = new Paragraph(" - Osservazioni sul tipo di alloggio: " + osser_abitazione + "\n");
				document.add(osservazioni_tipo);
			}
			Paragraph motivo = new Paragraph(" - Motivo del trasferimento: " + mot.toUpperCase() + "\n");
			document.add(motivo);
			if(mot.equals("altro")) {
				Paragraph motivo_causa = new Paragraph(" > Causa: " + mot_causa.toUpperCase() + "\n\n");
				document.add(motivo_causa);
			}
			
			document.add(spazio);
			PdfPTable tabella_professione = new PdfPTable(2);
			tabella_professione.addCell(new Paragraph("Professione o condizione non professionale dei componenti"));
			tabella_professione.addCell(new Paragraph("Indicare il luogo di lavoro o l'indirizzo della scuola frequentata"));
			tabella_professione.addCell(new Paragraph(professione));
			tabella_professione.addCell(new Paragraph(ind_lavoro));
			tabella_professione.setWidthPercentage(100);
			document.add(tabella_professione);
			
			if(transfer.length() != 0) {
				Paragraph altro_coniuge = new Paragraph(" - Quando il trasferimento si riferisce ad un solo coniuge (con o senza familiari) indicare l'indirizzo: " + transfer.toUpperCase() + "\n");
				document.add(altro_coniuge);
			}
			Paragraph desume = new Paragraph(" - Dalle informazioni sopra indicate si desume che sussista la dimora abituale? "+circostanze.toUpperCase()+"\n");
			document.add(desume);
			Paragraph osservazioni_finali = new Paragraph(" - Osservazioni: " + oss_finali + "\n\n\n");
			document.add(osservazioni_finali);
			document.add(sdata);
			document.add(firma_dichiarante);
			
			document.close();
			fout.close();
			
			if(cntlr.equals("stesso")) {
				aggiornaDB(indirnew, num_civnew);
			} else {
				cancellaDB(richiesta, risposta);
			}
			
		} catch (DocumentException e) {
			e.printStackTrace();
		}
	}

	private void aggiornaDB(String indirnew, String num_civnew) {
		DbCambioResidenza cr = new DbCambioResidenza();
		CartaIdentita ci = (CartaIdentita) session.getAttribute("ci");
		cr.modificaResidenceIn(ci.ottenereNumero(), indirnew, Integer.parseInt(num_civnew));
	}
	
	private void cancellaDB(HttpServletRequest richiesta, HttpServletResponse risposta) throws ServletException, IOException {
		AccessoManager AM = new AccessoManager();
		CittadinoManager CM = new CittadinoManager();
		Cittadino c = (Cittadino) session.getAttribute("c");
		
		if(AM.eliminaAccesso(c.ottenereLogin()) && CM.cancellaCittadino(c.ottenereIdCittadino())){	//elimina il cittadino e l'accesso 
			//controllando che l'esito sia positivo
			NucleoFamiliareManager NFM = new NucleoFamiliareManager();
			NFM.ottenereNComponentiNucleo(c.ottenereNucleoFamiliare());
			String ris="ok";
			ServletContext sc = getServletContext();
			richiesta.setAttribute("ris", ris);
			RequestDispatcher rd = sc.getRequestDispatcher("/workers/index.jsp?func=operazione&page=riuscita"); 
			rd.forward(richiesta, risposta);
		}
	}
}
