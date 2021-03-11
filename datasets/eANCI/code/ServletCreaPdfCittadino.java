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
 * La classe ServletCreaPdfCittadino un file PDF in base ai dati ricevuti da una pagina JSP
 * La classe non ha nessuna dipendenza
 * @author Christian Ronca
 */


public class ServletCreaPdfCittadino extends HttpServlet {
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
			String nome					= richiesta.getParameter("name").toUpperCase();
			String surname				= richiesta.getParameter("surname").toUpperCase();
			String name_citta			= richiesta.getParameter("citta").toUpperCase();
			String gg_date				= richiesta.getParameter("gg");
			String mm_date				= richiesta.getParameter("mm");
			String aa_date				= richiesta.getParameter("aa");
			String newcomune			= richiesta.getParameter("newcomune").toUpperCase();
			String indir				= richiesta.getParameter("via").toUpperCase();
			String numero_civico		= richiesta.getParameter("civico");
			String indirnew				= richiesta.getParameter("newvia").toUpperCase();
			String num_civnew			= richiesta.getParameter("num");
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
			String indirizzo			= richiesta.getParameter("indirizzo").toUpperCase();
			String num_civico1			= richiesta.getParameter("num_civico1");
			String prec_res				= richiesta.getParameter("prec_res").toUpperCase();
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
			
			cntlr = "stesso";
			if(cntlr.equals("stesso")) {
				inout = "interno";
			} else {
				inout = "altro";
			}
			
			Document document = new Document(PageSize.A4);
			PdfWriter.getInstance(document, risposta.getOutputStream());
			FileOutputStream fout = new FileOutputStream("webapps//myDocs//docs//" + now +"_2345_" + inout +".pdf");
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

			Paragraph sdata = new Paragraph("Data: "+gg+"/"+mm+"/"+year, new Font(Font.HELVETICA, 12, Font.NORMAL));
			sdata.setAlignment(Element.ALIGN_LEFT);
			document.add(sdata);
			
			Paragraph firma_dichiarante = new Paragraph("_________________\nFirma del dichiarante\n\n", new Font(Font.HELVETICA, 12, Font.NORMAL));
			firma_dichiarante.setAlignment(Element.ALIGN_RIGHT);
			document.add(firma_dichiarante);
			
			document.close();
		} catch(Exception e) {
			e.printStackTrace();
		}
	}
}