import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import logging

logger = logging.getLogger(__name__)


class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Section header style
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Label style for form fields
        self.label_style = ParagraphStyle(
            'CustomLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        # Value style for form fields
        self.value_style = ParagraphStyle(
            'CustomValue',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            leftIndent=20
        )
    
    def generate_application_pdf(self, application_data: Dict[str, Any], customer_data: Dict[str, Any], steps_data: list) -> str:
        """
        Generate a comprehensive PDF report for a completed onboarding application
        
        Args:
            application_data: Application information
            customer_data: Customer information
            steps_data: List of completed steps with their data
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Create temporary file for PDF
            temp_dir = tempfile.gettempdir()
            filename = f"application_{application_data['application_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(temp_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            story = []
            
            # Add title page
            story.extend(self._create_title_page(application_data))
            story.append(PageBreak())
            
            # Add application summary
            story.extend(self._create_application_summary(application_data))
            story.append(PageBreak())
            
            # Add personal information
            story.extend(self._create_personal_info_section(customer_data, steps_data))
            story.append(PageBreak())
            
            # Add contact information
            story.extend(self._create_contact_info_section(customer_data, steps_data))
            story.append(PageBreak())
            
            # Add financial profile
            story.extend(self._create_financial_profile_section(customer_data, steps_data))
            story.append(PageBreak())
            
            # Add documents section
            story.extend(self._create_documents_section(application_data))
            story.append(PageBreak())
            
            # Add eligibility results
            if application_data.get('eligibility_result'):
                story.extend(self._create_eligibility_section(application_data))
                story.append(PageBreak())
            
            # Add review information
            story.extend(self._create_review_section(application_data))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF generated successfully: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}")
            raise
    
    def _create_title_page(self, application_data: Dict[str, Any]) -> list:
        """Create the title page of the PDF"""
        story = []
        
        # Main title
        title = Paragraph("ONBOARDING APPLICATION REPORT", self.title_style)
        story.append(title)
        story.append(Spacer(1, 30))
        
        # Application details
        app_info = [
            ["Application Number:", application_data.get('application_number', 'N/A')],
            ["Status:", self._format_status(application_data.get('status', ''))],
            ["Created Date:", self._format_date(application_data.get('created_at'))],
            ["Submitted Date:", self._format_date(application_data.get('submitted_at'))],
            ["Completed Date:", self._format_date(application_data.get('completed_at'))]
        ]
        
        app_table = Table(app_info, colWidths=[2*inch, 4*inch])
        app_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        story.append(app_table)
        story.append(Spacer(1, 30))
        
        # Generated info
        generated_info = Paragraph(
            f"Report generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.normal_style
        )
        story.append(generated_info)
        
        return story
    
    def _create_application_summary(self, application_data: Dict[str, Any]) -> list:
        """Create application summary section"""
        story = []
        
        # Section header
        story.append(Paragraph("APPLICATION SUMMARY", self.section_style))
        story.append(Spacer(1, 12))
        
        # Progress information
        progress_info = [
            ["Current Step:", f"Step {application_data.get('current_step', 0)} of {application_data.get('total_steps', 0)}"],
            ["Progress:", f"{application_data.get('progress_percentage', 0):.1f}%"],
            ["Application Status:", self._format_status(application_data.get('status', ''))],
        ]
        
        if application_data.get('eligibility_result'):
            progress_info.extend([
                ["Credit Score:", str(application_data['eligibility_result'].get('score', 'N/A'))],
                ["Grade:", application_data['eligibility_result'].get('grade', 'N/A')],
                ["Eligibility:", application_data['eligibility_result'].get('eligibility', 'N/A')]
            ])
        
        progress_table = Table(progress_info, colWidths=[2*inch, 4*inch])
        progress_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        story.append(progress_table)
        
        return story
    
    def _create_personal_info_section(self, customer_data: Dict[str, Any], steps_data: list) -> list:
        """Create personal information section"""
        story = []
        
        # Section header
        story.append(Paragraph("PERSONAL INFORMATION", self.section_style))
        story.append(Spacer(1, 12))
        
        # Get personal info from steps data
        personal_step = next((step for step in steps_data if step.get('step_number') == 1), {})
        personal_data = personal_step.get('step_data', {})
        
        # Personal information fields
        personal_fields = [
            ("Full Name:", f"{personal_data.get('first_name', '')} {personal_data.get('last_name', '')}"),
            ("Date of Birth:", self._format_date(personal_data.get('date_of_birth'))),
            ("Gender:", personal_data.get('gender', '').title() if personal_data.get('gender') else 'N/A'),
            ("Marital Status:", personal_data.get('marital_status', '').title() if personal_data.get('marital_status') else 'N/A'),
            ("Nationality:", personal_data.get('nationality', 'N/A')),
            ("ID Number:", personal_data.get('id_number', 'N/A')),
            ("ID Type:", personal_data.get('id_type', 'N/A').replace('_', ' ').title()),
        ]
        
        for label, value in personal_fields:
            if value and value != 'N/A':
                story.append(Paragraph(label, self.label_style))
                story.append(Paragraph(value, self.value_style))
        
        return story
    
    def _create_contact_info_section(self, customer_data: Dict[str, Any], steps_data: list) -> list:
        """Create contact information section"""
        story = []
        
        # Section header
        story.append(Paragraph("CONTACT INFORMATION", self.section_style))
        story.append(Spacer(1, 12))
        
        # Get contact info from steps data
        contact_step = next((step for step in steps_data if step.get('step_number') == 2), {})
        contact_data = contact_step.get('step_data', {})
        
        # Contact information fields
        contact_fields = [
            ("Phone Number:", contact_data.get('phone_number', 'N/A')),
            ("Email Address:", contact_data.get('email', 'N/A')),
            ("Address Line 1:", contact_data.get('address_line1', 'N/A')),
            ("Address Line 2:", contact_data.get('address_line2', 'N/A') if contact_data.get('address_line2') else 'N/A'),
            ("City:", contact_data.get('city', 'N/A')),
            ("State/Province:", contact_data.get('state_province', 'N/A')),
            ("Postal Code:", contact_data.get('postal_code', 'N/A')),
            ("Country:", contact_data.get('country', 'N/A')),
        ]
        
        for label, value in contact_fields:
            if value and value != 'N/A':
                story.append(Paragraph(label, self.label_style))
                story.append(Paragraph(value, self.value_style))
        
        # Emergency contact
        story.append(Spacer(1, 12))
        story.append(Paragraph("Emergency Contact Information", self.label_style))
        story.append(Spacer(1, 6))
        
        emergency_fields = [
            ("Name:", contact_data.get('emergency_contact_name', 'N/A')),
            ("Phone:", contact_data.get('emergency_contact_phone', 'N/A')),
            ("Relationship:", contact_data.get('emergency_contact_relationship', 'N/A')),
        ]
        
        for label, value in emergency_fields:
            if value and value != 'N/A':
                story.append(Paragraph(label, self.label_style))
                story.append(Paragraph(value, self.value_style))
        
        return story
    
    def _create_financial_profile_section(self, customer_data: Dict[str, Any], steps_data: list) -> list:
        """Create financial profile section"""
        story = []
        
        # Section header
        story.append(Paragraph("FINANCIAL PROFILE", self.section_style))
        story.append(Spacer(1, 12))
        
        # Get financial info from steps data
        financial_step = next((step for step in steps_data if step.get('step_number') == 3), {})
        financial_data = financial_step.get('step_data', {})
        
        # Employment information
        story.append(Paragraph("Employment Information", self.label_style))
        story.append(Spacer(1, 6))
        
        employment_fields = [
            ("Employment Status:", financial_data.get('employment_status', '').replace('_', ' ').title() if financial_data.get('employment_status') else 'N/A'),
            ("Employer Name:", financial_data.get('employer_name', 'N/A')),
            ("Job Title:", financial_data.get('job_title', 'N/A')),
            ("Monthly Income:", f"${financial_data.get('monthly_income', 0):,.2f}" if financial_data.get('monthly_income') else 'N/A'),
            ("Employment Duration:", f"{financial_data.get('employment_duration_months', 0)} months" if financial_data.get('employment_duration_months') else 'N/A'),
        ]
        
        for label, value in employment_fields:
            if value and value != 'N/A':
                story.append(Paragraph(label, self.label_style))
                story.append(Paragraph(value, self.value_style))
        
        # Banking information
        story.append(Spacer(1, 12))
        story.append(Paragraph("Banking Information", self.label_style))
        story.append(Spacer(1, 6))
        
        banking_fields = [
            ("Bank Name:", financial_data.get('bank_name', 'N/A')),
            ("Account Number:", financial_data.get('bank_account_number', 'N/A')),
            ("Account Type:", financial_data.get('bank_account_type', '').title() if financial_data.get('bank_account_type') else 'N/A'),
        ]
        
        for label, value in banking_fields:
            if value and value != 'N/A':
                story.append(Paragraph(label, self.label_style))
                story.append(Paragraph(value, self.value_style))
        
        # Other loans
        story.append(Spacer(1, 12))
        story.append(Paragraph("Other Loans", self.label_style))
        story.append(Spacer(1, 6))
        
        has_other_loans = financial_data.get('has_other_loans', False)
        story.append(Paragraph("Has Other Loans:", self.label_style))
        story.append(Paragraph("Yes" if has_other_loans else "No", self.value_style))
        
        if has_other_loans and financial_data.get('other_loans_details'):
            story.append(Paragraph("Loan Details:", self.label_style))
            for loan in financial_data['other_loans_details']:
                loan_text = f"• {loan.get('lender', 'Unknown')} - {loan.get('amount', 'Unknown')} - {loan.get('status', 'Unknown')}"
                story.append(Paragraph(loan_text, self.value_style))
        
        return story
    
    def _create_documents_section(self, application_data: Dict[str, Any]) -> list:
        """Create documents section"""
        story = []
        
        # Section header
        story.append(Paragraph("DOCUMENTS", self.section_style))
        story.append(Spacer(1, 12))
        
        # Document information
        documents = application_data.get('documents', [])
        
        if documents:
            doc_data = []
            for doc in documents:
                doc_data.append([
                    Paragraph(doc.get('document_type', '').replace('_', ' ').title(), self.normal_style),
                    Paragraph(doc.get('document_name', 'N/A'), self.normal_style),
                    Paragraph(doc.get('status', '').title(), self.normal_style),
                    Paragraph(self._format_date(doc.get('uploaded_at')), self.normal_style)
                ])
            
            # Add headers
            headers = [[
                Paragraph("Document Type", self.label_style),
                Paragraph("Document Name", self.label_style),
                Paragraph("Status", self.label_style),
                Paragraph("Uploaded Date", self.label_style)
            ]]
            
            # Combine headers and data
            table_data = headers + doc_data
            
            # Set column widths for compactness
            col_widths = [1.2*inch, 2.2*inch, 1.0*inch, 1.2*inch]
            doc_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Table style for compactness and readability
            style = TableStyle([
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Header center
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),    # Body left
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ])
            # Add alternating row background colors
            for i in range(1, len(table_data)):
                if i % 2 == 1:
                    style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
                else:
                    style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
            doc_table.setStyle(style)
            
            story.append(doc_table)
        else:
            story.append(Paragraph("No documents uploaded", self.normal_style))
        
        return story
    
    def _create_eligibility_section(self, application_data: Dict[str, Any]) -> list:
        """Create eligibility results section"""
        story = []
        
        # Section header
        story.append(Paragraph("ELIGIBILITY RESULTS", self.section_style))
        story.append(Spacer(1, 12))
        
        eligibility = application_data.get('eligibility_result', {})
        
        eligibility_fields = [
            ("Credit Score:", str(eligibility.get('score', 'N/A'))),
            ("Grade:", eligibility.get('grade', 'N/A')),
            ("Eligibility Status:", eligibility.get('eligibility', 'N/A').title()),
            ("Message:", eligibility.get('message', 'N/A')),
        ]
        
        for label, value in eligibility_fields:
            if value and value != 'N/A':
                story.append(Paragraph(label, self.label_style))
                story.append(Paragraph(value, self.value_style))
        
        # Recommendations
        if eligibility.get('recommendations'):
            story.append(Spacer(1, 12))
            story.append(Paragraph("Recommendations:", self.label_style))
            for rec in eligibility['recommendations']:
                story.append(Paragraph(f"• {rec}", self.value_style))
        
        return story
    
    def _create_review_section(self, application_data: Dict[str, Any]) -> list:
        """Create review information section"""
        story = []
        
        # Section header
        story.append(Paragraph("REVIEW INFORMATION", self.section_style))
        story.append(Spacer(1, 12))
        
        review_fields = [
            ("Assigned Officer:", application_data.get('assigned_officer_name', 'N/A')),
            ("Review Notes:", application_data.get('review_notes', 'N/A')),
            ("Decision Made By:", application_data.get('decision_made_by_name', 'N/A')),
            ("Decision Date:", self._format_date(application_data.get('decision_date'))),
            ("Reviewed At:", self._format_date(application_data.get('reviewed_at'))),
        ]
        
        for label, value in review_fields:
            if value and value != 'N/A':
                story.append(Paragraph(label, self.label_style))
                story.append(Paragraph(value, self.value_style))
        
        # Rejection reason if applicable
        if application_data.get('rejection_reason'):
            story.append(Spacer(1, 12))
            story.append(Paragraph("Rejection Reason:", self.label_style))
            story.append(Paragraph(application_data['rejection_reason'], self.value_style))
        
        return story
    
    def _format_status(self, status: str) -> str:
        """Format status for display"""
        if not status:
            return 'N/A'
        return status.replace('_', ' ').title()
    
    def _format_date(self, date_value) -> str:
        """Format date for display"""
        if not date_value:
            return 'N/A'
        
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                return date_value
        
        if isinstance(date_value, datetime):
            return date_value.strftime('%B %d, %Y')
        
        return str(date_value) 