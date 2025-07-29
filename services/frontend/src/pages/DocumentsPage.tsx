import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, FileText } from 'lucide-react'

const DocumentsPage: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="text-muted-foreground">Manage your documents and files</p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Documents
            </CardTitle>
            <CardDescription>
              Upload new documents to the system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              Choose Files
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Recent Documents
            </CardTitle>
            <CardDescription>
              Your recently uploaded and accessed documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-muted-foreground">
              No documents found. Upload your first document to get started.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default DocumentsPage
