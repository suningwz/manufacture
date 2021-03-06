# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools, _

class RptTracing(models.Model):
    """
    View-mode model that ists data captured at checkpoints (data_win & data_wout) in order to be filtered by dates and exported to Excel
    """
    _name = 'mdc.rpt_tracing'
    _description = 'Tracing Report'
    _order = 'lot_name asc, employee_code asc, shift_code asc'
    _auto = False

    create_date = fields.Date('Date', readonly=True)
    lot_name = fields.Char('MO', readonly=True)
    employee_code = fields.Char('Employee Code', readonly=True)
    employee_name = fields.Char('Employee Name', readonly=True)
    contract_name = fields.Char('Contract Name', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    client_name = fields.Char('Client', readonly=True)
    shift_code = fields.Char('Shift Code', readonly=True)
    gross_weight = fields.Float('Gross', readonly=True, group_operator='sum')
    product_weight = fields.Float('Backs', readonly=True, group_operator='sum')
    sp1_weight = fields.Float('Crumbs', readonly=True, group_operator='sum')
    quality = fields.Float('Quality', readonly=True)
    total_hours = fields.Float('Total Hours', readonly=True, group_operator='sum')
    # TODO readonly=True
    std_yield_product = fields.Float('Std Yield Product')
    std_speed = fields.Float('Std Speed')
    std_yield_sp1 = fields.Float('Std Yield Subproduct 1')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as 
                SELECT woutdata.id, woutdata.create_date, lot.name as lot_name, lot.product_id, 
                    coalesce(cli.name,'') as client_name,
                    emp.employee_code, emp.name as employee_name, contr.name as contract_name, shift.shift_code, 
                    woutdata.gross_weight, woutdata.product_weight, woutdata.sp1_weight, 
                    case when woutdata.product_weight = 0 then 0 else woutdata.quality_weight/woutdata.product_weight end as quality,
                    lotemp.total_hours, 
                    lot.std_yield_product, lot.std_speed, lot.std_yield_sp1 
                    FROM (
                        SELECT
                            MIN(wout.id) as id,
                            date(wout.create_datetime) as create_date,
                            wout.lot_id, wout.employee_id, wout.shift_id, 
                            sum(wout.gross_weight) as gross_weight,
                            sum(case when woutcat.code='P' then wout.weight-wout.tare else 0 end) as product_weight,
                            sum(case when woutcat.code='SP1' then wout.weight-wout.tare else 0 end) as sp1_weight,
                            sum(case when woutcat.code='P' then qlty.code * (wout.weight-wout.tare) else 0 end) as quality_weight
                        FROM mdc_data_wout wout
                            LEFT JOIN mdc_wout_categ woutcat ON woutcat.id=wout.wout_categ_id 
                            LEFT JOIN mdc_quality qlty ON qlty.id=wout.quality_id
                        WHERE 1=1
                        GROUP BY 
                            date(wout.create_datetime),
                            wout.lot_id, wout.employee_id, wout.shift_id
                    ) woutdata
                    LEFT JOIN (SELECT 
                            date(ws.start_datetime) as start_date,
                            ws.lot_id, ws.employee_id, ws.shift_id, 
                            sum(ws.total_hours) as total_hours 
                        FROM mdc_worksheet ws
                        WHERE 1=1
                        GROUP BY date(ws.start_datetime),
                            ws.lot_id, ws.employee_id, ws.shift_id
                    ) lotemp ON lotemp.start_date=woutdata.create_date 
                            and lotemp.lot_id=woutdata.lot_id and lotemp.employee_id=woutdata.employee_id 
                            and lotemp.shift_id=woutdata.shift_id 
                    LEFT JOIN mdc_lot lot ON lot.id=woutdata.lot_id
                    LEFT JOIN res_partner cli on cli.id = lot.partner_id
                    LEFT JOIN hr_employee emp ON emp.id=woutdata.employee_id
                    LEFT JOIN hr_contract_type contr ON contr.id=emp.contract_type_id
                    LEFT JOIN mdc_shift shift ON shift.id=woutdata.shift_id  
                
        """ % self._table)

    # --------------- Calculate Grouped Values with Weighted average or complicated dropued formulas
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
               orderby=False, lazy=True):
        res = super(RptTracing, self).read_group(domain, fields, groupby,
             offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'quality' in fields:
            for line in res:
                if '__domain' in line:
                    quality_weight = 0
                    lines = self.search(line['__domain'])
                    for line_item in lines:
                        quality_weight += line_item.quality * line_item.product_weight
                    if line['product_weight'] > 0:
                        line['quality'] = quality_weight / line['product_weight']
        return res


class RptManufacturing(models.Model):
    """
    View-mode model that ists data captured at checkpoints (data_win & data_wout) in order to be filtered by dates and exported to Excel
    """
    _name = 'mdc.rpt_manufacturing'
    _description = 'Manufacturing Report'
    _order = 'lot_name asc, workstation_name asc, employee_code asc, shift_code asc'
    _auto = False

    create_date = fields.Date('Date', readonly=True)
    lot_name = fields.Char('MO', readonly=True)
    employee_code = fields.Char('Employee Code', readonly=True)
    employee_name = fields.Char('Employee Name', readonly=True)
    contract_name = fields.Char('Contract Name', readonly=True)
    workstation_name = fields.Char('Workstation Name', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    client_name = fields.Char('Client', readonly=True)
    shift_code = fields.Char('Shift Code', readonly=True)
    gross_weight = fields.Float('Gross', readonly=True, group_operator='sum')
    product_weight = fields.Float('Backs', readonly=True, group_operator='sum')
    sp1_weight = fields.Float('Crumbs', readonly=True, group_operator='sum')
    shared_gross_weight = fields.Float('Shared Gross', readonly=True, group_operator='sum')
    shared_product_weight = fields.Float('Shared Backs', readonly=True, group_operator='sum')
    shared_sp1_weight = fields.Float('Shared Crumbs', readonly=True, group_operator='sum')
    product_boxes = fields.Float('Box Backs', readonly=True, group_operator='sum')
    sp1_boxes = fields.Float('Box Crumbs', readonly=True, group_operator='sum')
    quality = fields.Float('Quality', readonly=True)
    total_hours = fields.Float('Total Hours', readonly=True, group_operator='sum')
    # TODO readonly=True
    std_yield_product = fields.Float('Std Yield Product')
    std_speed = fields.Float('Std Speed')
    std_yield_sp1 = fields.Float('Std Yield Subproduct 1')
    weight_std_lot = fields.Float('Std Weight Lot')
    coef_weight_lot = fields.Float('Coef Weight Lot')
    ind_backs = fields.Float('IND Backs', readonly=True, group_operator='avg')
    ind_mo = fields.Float('IND MO', readonly=True, group_operator='avg')
    ind_crumbs = fields.Float('IND Crumbs', readonly=True, group_operator='avg')
    ind_quality = fields.Float('IND Quality', readonly=True, group_operator='avg')
    ind_cleaning = fields.Float('IND Cleaning', readonly=True, group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as 
                SELECT woutdata.id, woutdata.create_date, lot.name as lot_name, lot.product_id,
                    coalesce(cli.name,'') as client_name,
                    emp.employee_code, emp.name as employee_name, contr.name as contract_name, shift.shift_code, 
                    woutdata.gross_weight, woutdata.product_weight, woutdata.sp1_weight, 
                    woutdata.shared_gross_weight, woutdata.shared_product_weight, woutdata.shared_sp1_weight,
                    case when (woutdata.product_weight + woutdata.shared_product_weight) = 0 then 0 else woutdata.quality_weight/(woutdata.product_weight + woutdata.shared_product_weight/2) end as quality,
                    wst.name as workstation_name, 
                    woutdata.product_boxes, woutdata.sp1_boxes, 
                    lotemp.total_hours, 
                    lot.std_yield_product, lot.std_speed, lot.std_yield_sp1,
                    lot.weight*(1-coalesce(lot.std_loss,0)/100) as weight_std_lot,
                    case when coalesce(lot.total_gross_weight,0) = 0 then 1 else lot.weight*(1-coalesce(lot.std_loss,0)/100)/lot.total_gross_weight end as coef_weight_lot,
                    case when coalesce(lot.std_yield_product,0)*woutdata.gross_weight = 0 then 0 else (woutdata.product_weight / woutdata.gross_weight) / lot.std_yield_product/ 1.15 end as ind_backs,
                    case when coalesce(lot.std_speed,0)*woutdata.gross_weight = 0 then 0 else (lotemp.total_hours * 60 / woutdata.gross_weight) / lot.std_speed / 1.15 end as ind_mo,
                    case when coalesce(woutdata.sp1_weight,0)*woutdata.gross_weight =0 then 0 else lot.std_yield_sp1 / (woutdata.sp1_weight / woutdata.gross_weight) / 1.15 end as ind_crumbs,
                    case when (woutdata.product_weight + woutdata.shared_product_weight)=0 then 0 else woutdata.quality_weight/(woutdata.product_weight + woutdata.shared_product_weight/2) end as ind_quality,
                    case when coalesce(lot.std_yield_product,0)*coalesce(lot.std_speed,0)*woutdata.gross_weight*woutdata.product_weight = 0 then 0 else
                    (0.6 *  ((woutdata.product_weight / woutdata.gross_weight) / lot.std_yield_product/ 1.15)) 
                    + (0.3 * ((lotemp.total_hours * 60 / woutdata.gross_weight) / lot.std_speed / 1.15)) 
                    + (0.1 * (woutdata.quality_weight / woutdata.product_weight)) end as ind_cleaning 
                    FROM (
                        SELECT
                            MIN(wout.id) as id,
                            date(wout.create_datetime) as create_date,
                            wout.lot_id, wout.employee_id, wout.shift_id, wout.workstation_id,
                            sum(case when wout.shared='false' then wout.gross_weight else 0 end) as gross_weight,
                            sum(case when wout.shared='false' and woutcat.code='P' then wout.weight-wout.tare else 0 end) as product_weight,
                            sum(case when wout.shared='false' and woutcat.code='SP1' then wout.weight-wout.tare else 0 end) as sp1_weight,
                            sum(case when wout.shared='true' then wout.gross_weight + shwout.gross_weight else 0 end) as shared_gross_weight,
                            sum(case when wout.shared='true' and woutcat.code='P' then wout.weight-wout.tare + shwout.weight-shwout.tare else 0 end) as shared_product_weight,
                            sum(case when wout.shared='true' and woutcat.code='SP1' then wout.weight-wout.tare + shwout.weight-shwout.tare else 0 end) as shared_sp1_weight,
                            sum(case when woutcat.code='P' then qlty.code * (wout.weight-wout.tare) else 0 end) as quality_weight,
                            sum(case when woutcat.code='P' then 1 else 0 end) as product_boxes,
                            sum(case when woutcat.code='SP1' then 1 else 0 end) as sp1_boxes
                        FROM mdc_data_wout wout
                            LEFT JOIN mdc_wout_categ woutcat ON woutcat.id=wout.wout_categ_id 
                            LEFT JOIN mdc_quality qlty ON qlty.id=wout.quality_id
                            LEFT JOIN mdc_data_wout shwout ON shwout.wout_shared_id=wout.id
                        WHERE 1=1
                        GROUP BY 
                            date(wout.create_datetime),
                            wout.lot_id, wout.employee_id, wout.shift_id, wout.workstation_id
                    ) woutdata
                    LEFT JOIN (SELECT 
                            date(ws.start_datetime) as start_date,
                            ws.lot_id, ws.employee_id, ws.shift_id, 
                            sum(ws.total_hours) as total_hours 
                        FROM mdc_worksheet ws
                        WHERE 1=1
                        GROUP BY date(ws.start_datetime),
                            ws.lot_id, ws.employee_id, ws.shift_id
                    ) lotemp ON lotemp.start_date=woutdata.create_date 
                            and lotemp.lot_id=woutdata.lot_id and lotemp.employee_id=woutdata.employee_id 
                            and lotemp.shift_id=woutdata.shift_id 
                    LEFT JOIN mdc_lot lot ON lot.id=woutdata.lot_id
                    LEFT JOIN res_partner cli on cli.id = lot.partner_id
                    LEFT JOIN hr_employee emp ON emp.id=woutdata.employee_id
                    LEFT JOIN hr_contract_type contr ON contr.id=emp.contract_type_id
                    LEFT JOIN mdc_shift shift ON shift.id=woutdata.shift_id
                    LEFT JOIN mdc_workstation wst ON wst.id=woutdata.workstation_id          
            
        """ % self._table)

    # --------------- Calculate Grouped Values with Weighted average or complicated dropued formulas
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        res = super(RptManufacturing, self).read_group(domain, fields, groupby,
                                                 offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'quality' in fields:
            for line in res:
                if '__domain' in line:
                    quality_weight = 0
                    total_weight = 0
                    lines = self.search(line['__domain'])
                    for line_item in lines:
                        quality_weight += line_item.quality * line_item.product_weight
                        total_weight += line_item.product_weight + line_item.shared_product_weight / 2
                    if total_weight > 0:
                        line['quality'] = quality_weight / total_weight
        return res


class RptIndicators(models.Model):
    """
    View-mode model that ists data captured at checkpoints (data_win & data_wout) in order to be filtered by dates and exported to Excel
    """
    _name = 'mdc.rpt_indicators'
    _description = 'Indicators Report'
    _order = 'lot_name asc, shift_code asc, employee_code asc'
    _auto = False

    create_date = fields.Date('Date', readonly=True)
    lot_name = fields.Char('MO', readonly=True)
    employee_code = fields.Char('Employee Code', readonly=True)
    employee_name = fields.Char('Employee Name', readonly=True)
    contract_name = fields.Char('Contract Name', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    client_name = fields.Char('Client', readonly=True)
    shift_code = fields.Char('Shift Code', readonly=True)
    gross_weight = fields.Float('Gross', readonly=True, group_operator='sum')
    product_weight = fields.Float('Backs', readonly=True, group_operator='sum')
    sp1_weight = fields.Float('Crumbs', readonly=True, group_operator='sum')
    shared_gross_weight = fields.Float('Shared Gross', readonly=True, group_operator='sum')
    shared_product_weight = fields.Float('Shared Backs', readonly=True, group_operator='sum')
    shared_sp1_weight = fields.Float('Shared Crumbs', readonly=True, group_operator='sum')
    product_boxes = fields.Float('Box Backs', readonly=True, group_operator='sum')
    sp1_boxes = fields.Float('Box Crumbs', readonly=True, group_operator='sum')
    quality = fields.Float('Quality', readonly=True)
    total_hours = fields.Float('Total Hours', readonly=True, group_operator='sum')
    # TODO readonly=True
    std_yield_product = fields.Float('Std Yield Product')
    std_speed = fields.Float('Std Speed')
    std_yield_sp1 = fields.Float('Std Yield Subproduct 1')
    ind_backs = fields.Float('IND Backs', readonly=True, group_operator='avg')
    ind_mo = fields.Float('IND MO', readonly=True, group_operator='avg')
    ind_crumbs = fields.Float('IND Crumbs', readonly=True, group_operator='avg')
    ind_quality = fields.Float('IND Quality', readonly=True, group_operator='avg')
    ind_cleaning = fields.Float('IND Cleaning', readonly=True, group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as 
                SELECT woutdata.id, woutdata.create_date, lot.name as lot_name, lot.product_id, 
                    coalesce(cli.name,'') as client_name,
                    emp.employee_code, emp.name as employee_name, contr.name as contract_name, shift.shift_code, 
                    woutdata.gross_weight, woutdata.product_weight, woutdata.sp1_weight, 
                    woutdata.shared_gross_weight, woutdata.shared_product_weight, woutdata.shared_sp1_weight,
                    case when (woutdata.product_weight + woutdata.shared_product_weight)=0 then 0 else woutdata.quality_weight/(woutdata.product_weight + woutdata.shared_product_weight/2) end as quality,
                    woutdata.product_boxes, woutdata.sp1_boxes, 
                    lotemp.total_hours, 
                    lot.std_yield_product, lot.std_speed, lot.std_yield_sp1, 
                    case when coalesce(lot.std_yield_product,0)*woutdata.gross_weight = 0 then 0 else (woutdata.product_weight / woutdata.gross_weight) / lot.std_yield_product/ 1.15 end as ind_backs,
                    case when coalesce(lot.std_speed,0)*woutdata.gross_weight = 0 then 0 else (lotemp.total_hours * 60 / woutdata.gross_weight) / lot.std_speed / 1.15 end as ind_mo,
                    case when coalesce(woutdata.sp1_weight,0)*woutdata.gross_weight =0 then 0 else lot.std_yield_sp1 / (woutdata.sp1_weight / woutdata.gross_weight) / 1.15 end as ind_crumbs,
                    case when (woutdata.product_weight + woutdata.shared_product_weight)=0 then 0 else woutdata.quality_weight/(woutdata.product_weight + woutdata.shared_product_weight/2) end as ind_quality,
                    case when coalesce(lot.std_yield_product,0)*coalesce(lot.std_speed,0)*woutdata.product_weight*woutdata.gross_weight = 0 then 0 else
                    (0.6 *  ((woutdata.product_weight / woutdata.gross_weight) / lot.std_yield_product/ 1.15)) 
                    + (0.3 * ((lotemp.total_hours * 60 / woutdata.gross_weight) / lot.std_speed / 1.15)) 
                    + (0.1 * (woutdata.quality_weight / woutdata.product_weight)) end as ind_cleaning 
                    FROM (
                        SELECT
                            MIN(wout.id) as id,
                            date(wout.create_datetime) as create_date,
                            wout.lot_id, wout.employee_id, wout.shift_id, 
                            sum(case when wout.shared='false' then wout.gross_weight else 0 end) as gross_weight,
                            sum(case when wout.shared='false' and woutcat.code='P' then wout.weight-wout.tare else 0 end) as product_weight,
                            sum(case when wout.shared='false' and woutcat.code='SP1' then wout.weight-wout.tare else 0 end) as sp1_weight,
                            sum(case when wout.shared='true' then wout.gross_weight + shwout.gross_weight else 0 end) as shared_gross_weight,
                            sum(case when wout.shared='true' and woutcat.code='P' then wout.weight-wout.tare + shwout.weight-shwout.tare else 0 end) as shared_product_weight,
                            sum(case when wout.shared='true' and woutcat.code='SP1' then wout.weight-wout.tare + shwout.weight-shwout.tare else 0 end) as shared_sp1_weight,
                            sum(case when woutcat.code='P' then qlty.code * (wout.weight-wout.tare) else 0 end) as quality_weight,
                            sum(case when woutcat.code='P' then 1 else 0 end) as product_boxes,
                            sum(case when woutcat.code='SP1' then 1 else 0 end) as sp1_boxes
                        FROM mdc_data_wout wout
                            LEFT JOIN mdc_wout_categ woutcat ON woutcat.id=wout.wout_categ_id 
                            LEFT JOIN mdc_quality qlty ON qlty.id=wout.quality_id
                            LEFT JOIN mdc_data_wout shwout ON shwout.wout_shared_id=wout.id
                        WHERE 1=1
                        GROUP BY 
                            date(wout.create_datetime),
                            wout.lot_id, wout.employee_id, wout.shift_id
                    ) woutdata
                    LEFT JOIN (SELECT 
                            date(ws.start_datetime) as start_date,
                            ws.lot_id, ws.employee_id, ws.shift_id, 
                            sum(ws.total_hours) as total_hours 
                        FROM mdc_worksheet ws
                        WHERE 1=1
                        GROUP BY date(ws.start_datetime),
                            ws.lot_id, ws.employee_id, ws.shift_id
                    ) lotemp ON lotemp.start_date=woutdata.create_date 
                            and lotemp.lot_id=woutdata.lot_id and lotemp.employee_id=woutdata.employee_id 
                            and lotemp.shift_id=woutdata.shift_id 
                    LEFT JOIN mdc_lot lot ON lot.id=woutdata.lot_id
                    LEFT JOIN res_partner cli on cli.id = lot.partner_id
                    LEFT JOIN hr_employee emp ON emp.id=woutdata.employee_id
                    LEFT JOIN hr_contract_type contr ON contr.id=emp.contract_type_id
                    LEFT JOIN mdc_shift shift ON shift.id=woutdata.shift_id
                    
        """ % self._table)

    # --------------- Calculate Grouped Values with Weighted average or complicated dropued formulas
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        res = super(RptIndicators, self).read_group(domain, fields, groupby,
                                                 offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'ind_quality' in fields:
            for line in res:
                if '__domain' in line:
                    ind_quality_weight = 0
                    total_weight = 0
                    lines = self.search(line['__domain'])
                    for line_item in lines:
                        ind_quality_weight += line_item.ind_quality * line_item.product_weight
                        total_weight += line_item.product_weight + line_item.shared_product_weight /2
                    if total_weight > 0:
                        line['ind_quality'] = ind_quality_weight / total_weight
        return res


class RptCumulative(models.Model):
    """
    View-mode model that ists data captured at checkpoints (data_win & data_wout) in order to be filtered by dates and exported to Excel
    """
    _name = 'mdc.rpt_cumulative'
    _description = 'Cumulative Report'
    _order = 'lot_name asc, employee_code asc'
    _auto = False

    create_date = fields.Date('Date', readonly=True)
    lot_name = fields.Char('MO', readonly=True)
    employee_code = fields.Char('Employee Code', readonly=True)
    employee_name = fields.Char('Employee Name', readonly=True)
    contract_name = fields.Char('Contract Name', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    client_name = fields.Char('Client', readonly=True)
    gross_weight = fields.Float('Gross', readonly=True, group_operator='sum')
    product_weight = fields.Float('Backs', readonly=True, group_operator='sum')
    sp1_weight = fields.Float('Crumbs', readonly=True, group_operator='sum')
    shared_gross_weight = fields.Float('Shared Gross', readonly=True, group_operator='sum')
    shared_product_weight = fields.Float('Shared Backs', readonly=True, group_operator='sum')
    shared_sp1_weight = fields.Float('Shared Crumbs', readonly=True, group_operator='sum')
    product_boxes = fields.Float('Box Backs', readonly=True, group_operator='sum')
    sp1_boxes = fields.Float('Box Crumbs', readonly=True, group_operator='sum')
    total_yield = fields.Float('Total Yield', readonly=True)
    quality = fields.Float('Quality', readonly=True)
    total_hours = fields.Float('Total Hours', readonly=True, group_operator='sum')
    # TODO readonly=True
    std_yield_product = fields.Float('Std Yield Product')
    std_speed = fields.Float('Std Speed')
    std_yield_sp1 = fields.Float('Std Yield Subproduct 1')
    ind_backs = fields.Float('IND Backs', readonly=True, group_operator='avg')
    ind_mo = fields.Float('IND MO', readonly=True, group_operator='avg')
    ind_crumbs = fields.Float('IND Crumbs', readonly=True, group_operator='avg')
    ind_quality = fields.Float('IND Quality', readonly=True, group_operator='avg')
    ind_cleaning = fields.Float('IND Cleaning', readonly=True, group_operator='avg')

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as 
                SELECT woutdata.id, woutdata.create_date, lot.name as lot_name, lot.product_id, 
                    coalesce(cli.name,'') as client_name,
                    emp.employee_code, emp.name as employee_name, contr.name as contract_name, 
                    woutdata.gross_weight, woutdata.product_weight, woutdata.sp1_weight, 
                    woutdata.shared_gross_weight, woutdata.shared_product_weight, woutdata.shared_sp1_weight,
                    case when (woutdata.product_weight + woutdata.shared_product_weight)=0 then 0 else woutdata.quality_weight/(woutdata.product_weight + woutdata.shared_product_weight/2) end as quality,
                    woutdata.product_boxes, woutdata.sp1_boxes,
                    case when woutdata.gross_weight = 0 then 0 else 100*(woutdata.product_weight + woutdata.sp1_weight) / woutdata.gross_weight end as total_yield,
                    lotemp.total_hours, 
                    lot.std_yield_product, lot.std_speed, lot.std_yield_sp1, 
                    case when coalesce(lot.std_yield_product,0)*woutdata.gross_weight = 0 then 0 else (woutdata.product_weight / woutdata.gross_weight) / lot.std_yield_product/ 1.15 end as ind_backs,
                    case when coalesce(lot.std_speed,0)*woutdata.gross_weight = 0 then 0 else (lotemp.total_hours * 60 / woutdata.gross_weight) / lot.std_speed / 1.15 end as ind_mo,
                    case when coalesce(woutdata.sp1_weight,0)*woutdata.gross_weight =0 then 0 else lot.std_yield_sp1 / (woutdata.sp1_weight / woutdata.gross_weight) / 1.15 end as ind_crumbs,
                    case when (woutdata.product_weight + woutdata.shared_product_weight)=0 then 0 else woutdata.quality_weight/(woutdata.product_weight + woutdata.shared_product_weight/2) end as ind_quality,
                    case when coalesce(lot.std_yield_product,0)*coalesce(lot.std_speed,0)*woutdata.product_weight*woutdata.gross_weight = 0 then 0 else
                    (0.6 *  ((woutdata.product_weight / woutdata.gross_weight) / lot.std_yield_product/ 1.15)) 
                    + (0.3 * ((lotemp.total_hours * 60 / woutdata.gross_weight) / lot.std_speed / 1.15)) 
                    + (0.1 * (woutdata.quality_weight / woutdata.product_weight)) end as ind_cleaning 
                    FROM (
                        SELECT
                            MIN(wout.id) as id,
                            date(wout.create_datetime) as create_date,
                            wout.lot_id, wout.employee_id, 
                            sum(case when wout.shared='false' then wout.gross_weight else 0 end) as gross_weight,
                            sum(case when wout.shared='false' and woutcat.code='P' then wout.weight-wout.tare else 0 end) as product_weight,
                            sum(case when wout.shared='false' and woutcat.code='SP1' then wout.weight-wout.tare else 0 end) as sp1_weight,
                            sum(case when wout.shared='true' then wout.gross_weight + shwout.gross_weight else 0 end) as shared_gross_weight,
                            sum(case when wout.shared='true' and woutcat.code='P' then wout.weight-wout.tare + shwout.weight-shwout.tare else 0 end) as shared_product_weight,
                            sum(case when wout.shared='true' and woutcat.code='SP1' then wout.weight-wout.tare + shwout.weight-shwout.tare else 0 end) as shared_sp1_weight,
                            sum(case when woutcat.code='P' then qlty.code * (wout.weight-wout.tare) else 0 end) as quality_weight,
                            sum(case when woutcat.code='P' then 1 else 0 end) as product_boxes,
                            sum(case when woutcat.code='SP1' then 1 else 0 end) as sp1_boxes
                        FROM mdc_data_wout wout
                            LEFT JOIN mdc_wout_categ woutcat ON woutcat.id=wout.wout_categ_id 
                            LEFT JOIN mdc_quality qlty ON qlty.id=wout.quality_id
                            LEFT JOIN mdc_data_wout shwout ON shwout.wout_shared_id=wout.id
                        WHERE 1=1
                        GROUP BY 
                            date(wout.create_datetime),
                            wout.lot_id, wout.employee_id
                    ) woutdata
                    LEFT JOIN (SELECT 
                            date(ws.start_datetime) as start_date,
                            ws.lot_id, ws.employee_id, 
                            sum(ws.total_hours) as total_hours 
                        FROM mdc_worksheet ws
                        WHERE 1=1
                        GROUP BY date(ws.start_datetime),
                            ws.lot_id, ws.employee_id
                    ) lotemp ON lotemp.start_date=woutdata.create_date 
                            and lotemp.lot_id=woutdata.lot_id and lotemp.employee_id=woutdata.employee_id  
                    LEFT JOIN mdc_lot lot ON lot.id=woutdata.lot_id
                    LEFT JOIN res_partner cli on cli.id = lot.partner_id
                    LEFT JOIN hr_employee emp ON emp.id=woutdata.employee_id
                    LEFT JOIN hr_contract_type contr ON contr.id=emp.contract_type_id
                           
        """ % self._table)

    # --------------- Calculate Grouped Values with Weighted average or complicated dropued formulas
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        res = super(RptCumulative, self).read_group(domain, fields, groupby,
                                                    offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'quality' in fields or 'total_yield' in fields:
            for line in res:
                if '__domain' in line:
                    quality_weight = 0
                    total_yield_weight = 0
                    total_weight = 0
                    lines = self.search(line['__domain'])
                    for line_item in lines:
                        quality_weight += line_item.quality * line_item.product_weight
                        total_yield_weight += line_item.total_yield * line_item.product_weight
                        total_weight += line_item.product_weight + line_item.shared_product_weight / 2
                    if total_weight > 0:
                        line['quality'] = quality_weight / total_weight
                        line['total_yield'] = total_yield_weight / total_weight
        return res
