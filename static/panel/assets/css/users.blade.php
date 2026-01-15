@extends("admin/main")
@section("content")
@section('pageTitle', 'Home') 
<!-- Main Content -->
<section class="content home">
    <div class="block-header">
        <div class="row">
            <div class="col-lg-7 col-md-6 col-sm-12">
                <h2>Users <small class="text-muted"></small> </h2>
            </div>
        </div>
    </div>
    <table class="table table-bordered responsive-table">
        <thead>
            <tr>
                <th style="width: 8%;">Sr. No.</th>
                <th>Name </th>
                <th>Company Name </th>
                <th>Business</th>
                <th>Contact No1</th>
                <th>What's Up No</th>
                <th>Email Id</th>
                <th>Status</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            <?PHP $i=0;  foreach($data as $user){     $i++;?>
            <tr>
                <td>{{$i}}</td>
                <td>{{ $user->name }}</td>
                <td>{{ $user->companyName }}</td> 
                <td>{{ $user->business }}</td>
                <td>{{ $user->contactNo1 }}</td>
                <td>{{ $user->whatsUpNo }}</td>
                <td>{{ $user->emailId }}</td>
                <td>{{ $user->whatsUpNo }}</td>
                <td>
					<?PHP 
						if($user->status == 1){
					?>
						<a href=""><label class="btn btn-success active">In-Active</label></a>
					<?PHP
					}else{
					?>
						<a href=""><label class="btn btn-danger active">Active</label></a>                    	
                    <?PHP
					}
					?>
                </td>
            </tr>
            <?PHP } ?>
        </tbody>
    </table>
    {{ $data->links() }} 
    </section>
@endsection