from django.contrib import admin
import breeze.models as breeze_models

admin.site.register(breeze_models.Rscripts)
admin.site.register(breeze_models.Jobs)
admin.site.register(breeze_models.UserProfile)
admin.site.register(breeze_models.DataSet)
admin.site.register(breeze_models.InputTemplate)
admin.site.register(breeze_models.Report)
admin.site.register(breeze_models.ReportType)
admin.site.register(breeze_models.Project)
admin.site.register(breeze_models.Post)
admin.site.register(breeze_models.Group)
# admin.site.register(breeze_models.Statistics)
# admin.site.register(breeze_models.ShinyApp)
admin.site.register(breeze_models.OffsiteUser)
# admin.site.register(breeze_models.ShinyReport, prepopulated_fields = { 'custom_header': ['title'], })
admin.site.register(breeze_models.ShinyReport )
admin.site.register(breeze_models.ShinyTag)
admin.site.register(breeze_models.ComputeClass)
admin.site.register(breeze_models.ComputeResource)
admin.site.register(breeze_models.EngineClass)


